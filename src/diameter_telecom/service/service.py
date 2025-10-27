from ..app_new.common import CommonThreadingApplication
from ..message import DiameterMessage
from ..session_manager import SessionManager
from ..app_context import get_session_manager
from ..apn import IpQueue, ip_to_bytes
from typing import List, Dict, Any
from ..subscriber import Subscriber, Subscribers
from ..session._diameter_session import DiameterSession
from ..session.gx import GxSession
from ..session.rx import RxSession
from ..session.sy import SySession
from diameter.message import Message
import logging
from ..constants import *
logger = logging.getLogger("diameter_telecom.service")
import time

class ApplicationService:
    """
    ApplicationService is a combination of applications of different app_ids.
    They share the same session manager and they can refer to each other when handling requests.
    """
    applications: List[CommonThreadingApplication]
    subscribers: Subscribers

    def __init__(self, applications: List[CommonThreadingApplication],
                    diameter_config: dict,
                    framed_ip_address_cidr: str = "192.168.1.0/24",
                    session_manager: SessionManager = None):
        app_ids = []
        for i in applications:
            if not isinstance(i, CommonThreadingApplication):
                raise ValueError(f"Application {i} is not a CommonThreadingApplication")
            if i.application_id in app_ids:
                raise ValueError(f"Application ID {i.application_id} is already in the list")
            app_ids.append(i.application_id)
        self.applications = applications
        self._applications_by_id = {i.application_id: i for i in applications}
        self.diameter_config = diameter_config
        self._avps = dict()
        self.framed_ip_address_cidr = framed_ip_address_cidr
        self.ip_queue = IpQueue(framed_ip_address_cidr)
        if not session_manager:
            session_manager = get_session_manager()
        self.session_manager = session_manager
        self.set_session_manager(session_manager)
        self.logger = logging.getLogger("diameter_telecom")

    @property
    def subscribers(self) -> Subscribers:
        return self.session_manager.subscribers

    def __repr__(self):
        return str(self.to_dict())

    def to_dict(self):
        service_dict = dict()
        service_dict['applications'] = []
        for application in self.applications:
            service_dict['applications'].append(application.to_dict())
        service_dict['session_manager_id'] = self.session_manager.id
        service_dict['subscribers_id'] = self.subscribers.id
        service_dict['diameter_config'] = self.diameter_config
        service_dict['framed_ip_address_cidr'] = self.framed_ip_address_cidr
        return service_dict

    @property
    def gx_app(self) -> CommonThreadingApplication:
        return self._applications_by_id.get(APP_3GPP_GX)

    @property
    def rx_app(self) -> CommonThreadingApplication:
        return self._applications_by_id.get(APP_3GPP_RX)

    @property
    def sy_app(self) -> CommonThreadingApplication:
        return self._applications_by_id.get(APP_3GPP_SY)

    def get_avps(self, app_id: int):
        return self.diameter_config.get(app_id, {})

    def add_avps(self, message: Message):
        app_id = message.header.application_id
        for key, value in self.get_avps(app_id).items():
            if hasattr(message, key):
                setattr(message, key, value)
        return message

    def set_session_manager(self, session_manager: SessionManager):
        self.session_manager = session_manager
        # self.subscribers = session_manager.subscribers
        for i in self.applications:
            i.set_session_manager(session_manager)

    # def set_subscribers(self, subscribers: Subscribers):
    #     # Delegate to session manager to keep single source of truth
    #     if hasattr(self.session_manager, 'set_subscribers'):
    #         self.session_manager.set_subscribers(subscribers)
    #     self.subscribers = self.session_manager.subscribers
    #     for i in self.applications:
    #         i.set_subscribers(self.subscribers)

    # delegates to the application
    def create_session(self, app_id: int, subscriber: Subscriber) -> DiameterSession:
        app: CommonThreadingApplication = self._applications_by_id.get(app_id)
        if not app:
            raise ValueError(f"Application ID {app_id} not found")
        if not hasattr(app, "create_session"):
            raise ValueError(f"Application {app_id} does not have a create_session method")
        diameter_session = app.create_session(subscriber)
        if hasattr(diameter_session, "framed_ip_address") and not diameter_session.framed_ip_address:
            diameter_session.framed_ip_address = self.ip_queue.get_ip()
        return diameter_session

    def create_gx_session(self, subscriber: Subscriber) -> GxSession:
        return self.create_session(APP_3GPP_GX, subscriber)

    def create_rx_session(self, subscriber: Subscriber) -> RxSession:
        return self.create_session(APP_3GPP_RX, subscriber)

    def create_sy_session(self, subscriber: Subscriber) -> SySession:
        return self.create_session(APP_3GPP_SY, subscriber)

    def _create_request(self, app_id: int, session: DiameterSession, goal: str = "create") -> Message:
        if goal not in ["create", "update", "terminate"]:
            raise ValueError(f"Goal {goal} not found")
        if not isinstance(session, DiameterSession):
            raise ValueError(f"Session is not a DiameterSession")
        app: CommonThreadingApplication = self._applications_by_id.get(app_id)
        if not app:
            raise ValueError(f"Application ID {app_id} not found")
        if not hasattr(app, "create_request"):
            raise ValueError(f"Application {app_id} does not have a create_request method")
        if goal == "create":
            request = app.create_request(app.MESSAGE_CREATE_SESSION, session)
        elif goal == "update":
            request = app.create_request(app.MESSAGE_UPDATE_SESSION, session)
        elif goal == "terminate":
            request = app.create_request(app.MESSAGE_TERMINATE_SESSION, session)
        elif goal == "refresh":
            request = app.create_request(app.MESSAGE_REFRESH_SESSION, session)
        return request

    def start_session(self, app_id: int, session: DiameterSession, request: Message = None) -> DiameterSession:
        app = self._applications_by_id.get(app_id)
        if not app:
            raise ValueError(f"Application ID {app_id} not found")
        if not hasattr(app, "create_request"):
            raise ValueError(f"Application {app_id} does not have a create_request method")
        if not session:
            raise ValueError(f"Session not found")
        if not isinstance(session, DiameterSession):
            raise ValueError(f"Session is not a DiameterSession")
        if not request:
            request: Message = self._create_request(app_id, session, goal="create")
        logger.debug(f"First layer of AVPS (application)")
        request = app.add_avps(request)
        # for key, value in app.avps.items():
        #     if hasattr(request, key):
        #         setattr(request, key, value)
        logger.debug(f"Second layer of AVPS (session)")
        request = session.add_avps(request)
        # for key, value in session.avps.items():
        #     if hasattr(request, key):
        #         setattr(request, key, value)
        logger.debug(f"Third layer of AVPS (service)")
        request = self.add_avps(request)
        logger.debug(f"Fourth layer of AVPS (subscriber)")
        request = session.subscriber.add_avps(request)
        answer = app.send_request_custom(request)
        time.sleep(1)
        if answer.result_code != E_RESULT_CODE_DIAMETER_SUCCESS:
            self.logger.error(f"Failed to start session {session.session_id} for application {app_id}. Result code: {answer.result_code}. Triggering termination.")
            self.terminate_session(app_id, session)
            raise ValueError(f"Failed to start session {session.session_id} for application {app_id}. Result code: {answer.result_code}")
        return session

    def start_diameter_session(self, session: DiameterSession):
        app_id = session.app_id
        return self.start_session(app_id, session)

    def update_session(self, app_id: int, session: DiameterSession, avps_list: List[Dict[str, Any]] = None, request: Message = None):
        app = self._applications_by_id.get(app_id)
        if not app:
            raise ValueError(f"Application ID {app_id} not found")
        if not hasattr(app, "create_request"):
            raise ValueError(f"Application {app_id} does not have a update_session method")
        if not request:
            request = self._create_request(app_id, session, goal="update")
        for key, value in app.avps.items():
            logger.debug(f"First layer of AVPS (application): {key} = {value}")
            if hasattr(request, key):
                setattr(request, key, value)
        for key, value in session.avps.items():
            logger.debug(f"Second layer of AVPS (session): {key} = {value}")
            if hasattr(request, key):
                setattr(request, key, value)
        for key, value in self.get_avps(app_id).items():
            logger.debug(f"Third layer of AVPS (service): {key} = {value}")
            if hasattr(request, key):
                setattr(request, key, value)
        for key, value in session.subscriber.avps.items():
            logger.debug(f"Fourth layer of AVPS (subscriber): {key} = {value}")
            if hasattr(request, key):
                setattr(request, key, value)
        if avps_list:
            for i in avps_list:
                avp_name = i.get("name")
                avp_value = i.get("value")
                if hasattr(request, avp_name):
                    setattr(request, avp_name, avp_value)
        answer = app.send_request_custom(request)
        if answer.result_code != E_RESULT_CODE_DIAMETER_SUCCESS:
            self.logger.error(f"Failed to update session {session.session_id} for application {app_id}. Result code: {answer.result_code}. Triggering termination.")
            self.terminate_session(app_id, session)
            raise ValueError(f"Failed to update session {session.session_id} for application {app_id}. Result code: {answer.result_code}")
        return session

    def terminate_session(self, app_id: int, session: DiameterSession):
        app = self._applications_by_id.get(app_id)
        if not app:
            raise ValueError(f"Application ID {app_id} not found")
        if not hasattr(app, "create_request"):
            raise ValueError(f"Application {app_id} does not have a terminate_session method")
        # request: Message = app.create_request(app.MESSAGE_TERMINATE_SESSION, session)
        request = self._create_request(app_id, session, goal="terminate")
        for key, value in self.get_avps(app_id).items():
            if hasattr(request, key):
                setattr(request, key, value)
        answer = app.send_request_custom(request)
        if answer.result_code != E_RESULT_CODE_DIAMETER_SUCCESS:
            self.logger.error(f"Failed to terminate session {session.session_id} for application {app_id}. Result code: {answer.result_code}")
        return session
                
    def refresh_session(self, app_id: int, session: DiameterSession):
        app = self._applications_by_id.get(app_id)
        if not app:
            raise ValueError(f"Application ID {app_id} not found")
        if not hasattr(app, "create_request"):
            raise ValueError(f"Application {app_id} does not have a refresh_session method")
        request = self._create_request(app_id, session, goal="refresh")
        return app.send_request_custom(request)

    def start(self):
        for i in self.applications:
            if not i.node._started:
                i.node.start()

    def wait_for_ready(self):
        for i in self.applications:
            i.wait_for_ready(5)

    def stop(self):
        for i in self.applications:
            if i.node._started:
                i.node.stop()
 
