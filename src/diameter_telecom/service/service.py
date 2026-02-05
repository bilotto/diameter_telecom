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
import time

logger = logging.getLogger("diameter_telecom.services")

from diameter.message import dump

class ApplicationService:
    """
    ApplicationService is a combination of applications of different app_ids.
    They share the same session manager and they can refer to each other when handling requests.
    """
    applications: List[CommonThreadingApplication]

    def __init__(self, applications: List[CommonThreadingApplication],
                    diameter_config: dict,
                    framed_ip_address_cidr: str = "192.168.1.0/24",
                    session_manager: SessionManager = None):
        app_ids = []
        for i in applications:
            # if not isinstance(i, CommonThreadingApplication):
            #     raise ValueError(f"Application {i} is not a CommonThreadingApplication")
            if i.application_id in app_ids:
                raise ValueError(f"Application ID {i.application_id} is already in the list")
            app_ids.append(i.application_id)
        self.applications = applications
        self._applications_by_id = {i.application_id: i for i in applications}
        self.diameter_config = diameter_config
        self._avps = dict[Any, Any]()
        self.framed_ip_address_cidr = framed_ip_address_cidr
        self.ip_queue = IpQueue(framed_ip_address_cidr)
        if not session_manager:
            session_manager = get_session_manager()
        self.session_manager = session_manager
        self.set_session_manager(session_manager)
        self.logger = logger
        self.confirm_message_mode = False

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
            self.logger.debug(f"Adding AVP: {key} = {value}")
            if hasattr(message, key):
                setattr(message, key, value)
        # If the message has framed_ip_address and its not set, we will need to find the IP address to put it there.
        # if hasattr(message, "framed_ip_address") and not message.framed_ip_address:
        #     message.framed_ip_address = self.ip_queue.get_ip()
        return message

    def _apply_avp_layers(self, app_id: int, session: DiameterSession, request: Message, 
                         custom_avps: List[Dict[str, Any]] = None,
                         apply_application: bool = True,
                         apply_session: bool = True, 
                         apply_service: bool = True,
                         apply_subscriber: bool = True) -> Message:
        """
        Apply AVP layers to a Diameter request message.
        
        Args:
            app_id: Application ID
            session: Diameter session
            request: Message to apply AVPs to
            custom_avps: Optional list of custom AVPs to apply
            apply_application: Whether to apply application layer AVPs
            apply_session: Whether to apply session layer AVPs
            apply_service: Whether to apply service layer AVPs
            apply_subscriber: Whether to apply subscriber layer AVPs
            
        Returns:
            Message with AVPs applied
        """
        app = self._applications_by_id.get(app_id)
        if not app:
            raise ValueError(f"Application ID {app_id} not found")
            
        if apply_application:
            self.logger.debug(f"{app_id}, {session.session_id}: First layer of AVPS (application)")
            request = app.add_avps(request)
            
        if apply_session:
            self.logger.debug(f"{app_id}, {session.session_id}: Second layer of AVPS (session)")
            request = session.add_avps(request)
            
        if apply_service:
            self.logger.debug(f"{app_id}, {session.session_id}: Third layer of AVPS (service)")
            request = self.add_avps(request)
            
        if apply_subscriber:
            self.logger.debug(f"{app_id}, {session.session_id}: Fourth layer of AVPS (subscriber)")
            request = session.subscriber.add_avps(request)
            
        if custom_avps:
            self.logger.debug(f"{app_id}, {session.session_id}: Custom AVPS")
            for avp in custom_avps:
                avp_name = avp.get("name")
                avp_value = avp.get("value")
                if hasattr(request, avp_name):
                    setattr(request, avp_name, avp_value)
                    self.logger.debug(f"Custom AVP: {avp_name} = {avp_value}")
                    
        return request

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
        self.logger.debug(f"Creating session for application {app_id} and subscriber {subscriber.msisdn}")
        app: CommonThreadingApplication = self._applications_by_id.get(app_id)
        if not app:
            raise ValueError(f"Application ID {app_id} not found")
        if not hasattr(app, "create_session"):
            raise ValueError(f"Application {app_id} does not have a create_session method")
        diameter_session = app.create_session(subscriber)
        if hasattr(diameter_session, "framed_ip_address") and not diameter_session.framed_ip_address:
            diameter_session.framed_ip_address = self.ip_queue.get_ip()
        self.logger.debug(f"Session created: {diameter_session}")
        return diameter_session

    def create_gx_session(self, subscriber: Subscriber) -> GxSession:
        self.logger.debug(f"Creating GX session for subscriber {subscriber.msisdn}")
        return self.create_session(APP_3GPP_GX, subscriber)

    def create_rx_session(self, subscriber: Subscriber) -> RxSession:
        self.logger.debug(f"Creating RX session for subscriber {subscriber.msisdn}")
        return self.create_session(APP_3GPP_RX, subscriber)

    def create_sy_session(self, subscriber: Subscriber) -> SySession:
        self.logger.debug(f"Creating SY session for subscriber {subscriber.msisdn}")
        return self.create_session(APP_3GPP_SY, subscriber)

    def _create_request(self, app_id: int, session: DiameterSession, goal: str = "create") -> Message:
        self.logger.debug(f"Creating request for session {session.session_id} for application {app_id} with goal {goal}")
        if goal not in ["create", "update", "terminate", "refresh", "abort"]:
            raise ValueError(f"Goal {goal} not found")
        if not isinstance(session, DiameterSession):
            raise ValueError(f"Session is not a DiameterSession")
        app: CommonThreadingApplication = self._applications_by_id.get(app_id)
        if not app:
            raise ValueError(f"Application ID {app_id} not found")
        if not hasattr(app, "create_request"):
            raise ValueError(f"Application {app_id} does not have a create_request method")
        if goal == "create":
            request: Message = app.create_request(app.MESSAGE_CREATE_SESSION, session)
        elif goal == "update":
            request: Message = app.create_request(app.MESSAGE_UPDATE_SESSION, session)
        elif goal == "terminate":
            request: Message = app.create_request(app.MESSAGE_TERMINATE_SESSION, session)
        elif goal == "refresh":
            request: Message = app.create_request(app.MESSAGE_REFRESH_SESSION, session)
        elif goal == "abort":
            request: Message = app.create_request(app.MESSAGE_ABORT_SESSION, session)
            pass
        self.logger.debug(f"Request created: {request}")
        if not request.header.end_to_end_identifier:
            request.header.end_to_end_identifier = app.node.end_to_end_seq.next_sequence()
        return request

    def send_request(self, request: Message) -> DiameterMessage:
        app_id = request.header.application_id
        app = self._applications_by_id.get(app_id)
        if not app:
            raise ValueError(f"Application ID {app_id} not found")
        if not hasattr(app, "send_request_custom"):
            raise ValueError(f"Application {app_id} does not have a send_request_custom method")
        if self.confirm_message_mode:
            print(f"The following message will be sent: {dump(request)}")
            confirm = input("Confirm message? (y/n): ")
            if confirm != "y":
                raise ValueError(f"Message not confirmed")
        # request = apply_avp_layers(request, app)
        # request = self.add_avps(request)
        return app.send_request_custom(request)

    def start_session(self, app_id: int, session: DiameterSession, request: Message = None, custom_avps: List[Dict[str, Any]] = None) -> DiameterSession:
        self.logger.debug(f"Starting session {session.session_id} for application {app_id}")
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
        
        # Apply all AVP layers for session start
        # request = self._apply_avp_layers(app_id, session, request, custom_avps=custom_avps)
        request = apply_avp_layers(request, app=app, session=session, subscriber=session.subscriber, service=self, custom_avps=custom_avps)
        self.session_manager.sessions.add_session(app_id, session)
        # answer = app.send_request_custom(request)
        answer = self.send_request(request)
        # time.sleep(1)
        # if answer.result_code != E_RESULT_CODE_DIAMETER_SUCCESS:
        #     self.logger.error(f"Failed to start session {session.session_id} for application {app_id}. Result code: {answer.result_code}. Triggering termination.")
        #     self.terminate_session(app_id, session)
        #     raise ValueError(f"Failed to start session {session.session_id} for application {app_id}. Result code: {answer.result_code}")
        self.logger.debug(f"{app_id}, {session.session_id}: Session started")
        return session

    def start_diameter_session(self, session: DiameterSession, custom_avps: List[Dict[str, Any]] = None):
        app_id = session.app_id
        return self.start_session(app_id, session, custom_avps=custom_avps)

    def update_session(self, app_id: int, session: DiameterSession, avps_list: List[Dict[str, Any]] = None, 
                      request: Message = None, apply_subscriber: bool = False) -> DiameterSession:
        app = self._applications_by_id.get(app_id)
        if not app:
            raise ValueError(f"Application ID {app_id} not found")
        if not hasattr(app, "create_request"):
            raise ValueError(f"Application {app_id} does not have a update_session method")
        if not request:
            request = self._create_request(app_id, session, goal="update")
        request = apply_avp_layers(request, app=app, session=session, subscriber=session.subscriber, service=self, custom_avps=avps_list)
        # answer = app.send_request_custom(request)
        answer = self.send_request(request)
        # if answer.result_code != E_RESULT_CODE_DIAMETER_SUCCESS:
        #     self.logger.error(f"Failed to update session {session.session_id} for application {app_id}. Result code: {answer.result_code}. Triggering termination.")
        #     self.terminate_session(app_id, session)
        #     raise ValueError(f"Failed to update session {session.session_id} for application {app_id}. Result code: {answer.result_code}")
        return session

    def terminate_session(self, app_id: int, session: DiameterSession) -> DiameterSession:
        app = self._applications_by_id.get(app_id)
        if not app:
            raise ValueError(f"Application ID {app_id} not found")
        if not hasattr(app, "create_request"):
            raise ValueError(f"Application {app_id} does not have a terminate_session method")
        
        if not app.SESSION_STARTER:
            print(f"Application {app_id} is not a session starter")
            return None
            
        request = self._create_request(app_id, session, goal="terminate")
        
        # Apply all AVP layers for session termination
        # request = self._apply_avp_layers(app_id, session, request, apply_subscriber=False, apply_session=False)
        request = apply_avp_layers(request, app=app, session=session, subscriber=None, service=self, custom_avps=None)
        # answer = app.send_request_custom(request)
        answer = self.send_request(request)
        # if answer.result_code != E_RESULT_CODE_DIAMETER_SUCCESS:
        #     self.logger.error(f"Failed to terminate session {session.session_id} for application {app_id}. Result code: {answer.result_code}")
        return session


    def _terminate_session(self, session: DiameterSession) -> DiameterSession:
        app_id = session.app_id
        app = self._applications_by_id.get(app_id)
        if not app:
            raise ValueError(f"Application ID {app_id} not found")
        if not hasattr(app, "create_request"):
            raise ValueError(f"Application {app_id} does not have a terminate_session method")
        
        if not app.SESSION_STARTER:
            print(f"Application {app_id} is not a session starter")
            return None
            
        request = self._create_request(app_id, session, goal="terminate")
        
        # Apply all AVP layers for session termination
        # request = self._apply_avp_layers(app_id, session, request, apply_subscriber=False, apply_session=False)
        request = apply_avp_layers(request, app=app, session=session, subscriber=None, service=self, custom_avps=None)
        # answer = app.send_request_custom(request)
        answer = self.send_request(request)
        # if answer.result_code != E_RESULT_CODE_DIAMETER_SUCCESS:
        #     self.logger.error(f"Failed to terminate session {session.session_id} for application {app_id}. Result code: {answer.result_code}")
        return session
                
    def refresh_session(self, app_id: int, session: DiameterSession):
        app = self._applications_by_id.get(app_id)
        if not app:
            raise ValueError(f"Application ID {app_id} not found")
        if not hasattr(app, "create_request"):
            raise ValueError(f"Application {app_id} does not have a refresh_session method")
        request = self._create_request(app_id, session, goal="refresh")
        # Apply all AVP layers for session refresh
        request = self._apply_avp_layers(app_id, session, request)
        # return app.send_request_custom(request)
        answer = self.send_request(request)
        return session


    def abort_session(self, app_id: int, session: DiameterSession):
        app = self._applications_by_id.get(app_id)
        if not app:
            raise ValueError(f"Application ID {app_id} not found")
        if not hasattr(app, "create_request"):
            raise ValueError(f"Application {app_id} does not have a abort_session method")
        request = self._create_request(app_id, session, goal="abort")
        request = apply_avp_layers(request, app=app, session=session, subscriber=None, service=self, custom_avps=None)
        answer = self.send_request(request)
        return session

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
 
    def terminate_all_sessions(self):
        try:
            for k, v in self.session_manager.sessions.sessions_index.items():
                app_id, session_id = k
                session = v
                self.terminate_session(app_id, session)
        except Exception as e:
            print(f"Error terminating all sessions: {e}")
            return False
        return True


def apply_avp_layers(request: Message,
                    app: CommonThreadingApplication = None,
                    session: DiameterSession = None,
                    subscriber: Subscriber = None,
                    service: ApplicationService = None,
                    custom_avps: List[Dict[str, Any]] = None) -> Message:
    """
    Apply AVP layers to a Diameter request message.
    
    Args:
        request: Message to apply AVPs to
        app: Application to apply AVPs to
        session: Diameter session to apply AVPs to
        subscriber: Subscriber to apply AVPs to
        custom_avps: Optional list of custom AVPs to apply
        
    Returns:
        Message with AVPs applied
    """

    if app:
        logger.debug(f"Applying Application Layer AVPS")
        request = app.add_avps(request)
    if session:
        logger.debug(f"Applying Session Layer AVPS")
        request = session.add_avps(request)
    if subscriber:
        logger.debug(f"Applying Subscriber Layer AVPS")
        request = subscriber.add_avps(request)
    if service:
        logger.debug(f"Applying Service Layer AVPS")
        request = service.add_avps(request)
    if custom_avps:
        logger.debug(f"Applying custom AVPs")
        for avp in custom_avps:
            avp_name = avp.get("name")
            avp_value = avp.get("value")
            if hasattr(request, avp_name):
                setattr(request, avp_name, avp_value)
                logger.debug(f"Custom AVP: {avp_name} = {avp_value}")
                
    return request