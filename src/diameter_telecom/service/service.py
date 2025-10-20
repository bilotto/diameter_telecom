from diameter_telecom.session_manager.session_manager import SessionManager


from ..app_new.common import CommonThreadingApplication
from ..message import DiameterMessage
from ..session_manager import SessionManager
from ..apn import IpQueue, ip_to_bytes
import time
from typing import List, Dict, Any
from ..subscriber import Subscriber, Subscribers
from ..session._diameter_session import DiameterSession
from diameter.message import Message
import logging
from ..constants import *
logger = logging.getLogger("diameter_telecom.service")

class ApplicationService:
    """
    ApplicationService is a combination of applications of different app_ids.
    They share the same session manager and they can refer to each other when handling requests.
    """
    applications: List[CommonThreadingApplication]
    subscribers: Subscribers

    def __init__(self, applications: List[CommonThreadingApplication], diameter_config: dict, framed_ip_address_cidr: str = "192.168.1.0/24", session_manager: SessionManager = None, subscribers: Subscribers = None):
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
            session_manager: SessionManager = SessionManager()
        if not subscribers:
            subscribers: Subscribers = Subscribers()
        self.session_manager = session_manager
        self.subscribers = subscribers
        self.set_session_manager(session_manager)
        self.set_subscribers(subscribers)
        for i in self.applications:
            for j in self.applications:
                if i.application_id != j.application_id:
                    i.related_apps.append(j)

        self.logger = logging.getLogger("diameter_telecom")

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

    def set_session_manager(self, session_manager: SessionManager):
        self.session_manager = session_manager
        for i in self.applications:
            i.set_session_manager(session_manager)

    def set_subscribers(self, subscribers: Subscribers):
        self.subscribers = subscribers
        for i in self.applications:
            i.set_subscribers(subscribers)

    # delegates to the application
    def create_session(self, app_id: int, subscriber: Subscriber) -> DiameterSession:
        app = self._applications_by_id.get(app_id)
        if not app:
            raise ValueError(f"Application ID {app_id} not found")
        if not hasattr(app, "create_session"):
            raise ValueError(f"Application {app_id} does not have a create_session method")
        return app.create_session(subscriber)

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
            return app.create_request(app.MESSAGE_CREATE_SESSION, session)
        elif goal == "update":
            return app.create_request(app.MESSAGE_UPDATE_SESSION, session)
        elif goal == "terminate":
            return app.create_request(app.MESSAGE_TERMINATE_SESSION, session)

    def start_session(self, app_id: int, session: DiameterSession):
        app = self._applications_by_id.get(app_id)
        if not app:
            raise ValueError(f"Application ID {app_id} not found")
        if not hasattr(app, "create_request"):
            raise ValueError(f"Application {app_id} does not have a create_request method")
        if not session:
            raise ValueError(f"Session not found")
        if not isinstance(session, DiameterSession):
            raise ValueError(f"Session is not a DiameterSession")
        # request: Message = app.create_request(app.MESSAGE_CREATE_SESSION, session)
        request = self._create_request(app_id, session, goal="create")
        # avps = self._avps.get(app_id, {})
        # destination_realm = self.diameter_config.get("destination_realm", app.node.realm_name)
        # request.destination_realm = destination_realm.encode()
        for key, value in self.get_avps(app_id).items():
            logger.debug(f"Updating session {session.session_id} with AVPS: {key} = {value}")
            if hasattr(request, key):
                setattr(request, key, value)
        return app.send_request_custom(request)

    def update_session(self, app_id: int, session: DiameterSession, avps_list: List[Dict[str, Any]] = None):
        app = self._applications_by_id.get(app_id)
        if not app:
            raise ValueError(f"Application ID {app_id} not found")
        if not hasattr(app, "create_request"):
            raise ValueError(f"Application {app_id} does not have a update_session method")
        # request: Message = app.create_request(app.MESSAGE_UPDATE_SESSION, session)
        request = self._create_request(app_id, session, goal="update")
        for key, value in self.get_avps(app_id).items():
            if hasattr(request, key):
                setattr(request, key, value)
        if avps_list:
            for i in avps_list:
                avp_name = i.get("name")
                avp_value = i.get("value")
                if hasattr(request, avp_name):
                    setattr(request, avp_name, avp_value)
        return app.send_request_custom(request)

    def terminate_session(self, app_id: int, session: DiameterSession):
        app = self._applications_by_id.get(app_id)
        if not app:
            raise ValueError(f"Application ID {app_id} not found")
        if not hasattr(app, "create_request"):
            raise ValueError(f"Application {app_id} does not have a terminate_session method")
        # request: Message = app.create_request(app.MESSAGE_TERMINATE_SESSION, session)
        request = self._create_request(app_id, session, goal="terminate")
        for key, value in self.get_avps(app_id).items():
            print(key, value)
            if hasattr(request, key):
                setattr(request, key, value)
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