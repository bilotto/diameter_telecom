from ..diameter.app_new.common import CommonThreadingApplication
from ..diameter.message import DiameterMessage
from ..diameter.session_manager import SessionManager
from ..apn import IpQueue, ip_to_bytes
import time
from typing import List
# from ..diameter.app import GxSession
# from ..diameter.app import CreditControlRequest
from ..subscriber import Subscriber, Subscribers
from ..diameter.session import DiameterSession
from diameter.message import Message
import logging

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
            if i.application_id in app_ids:
                raise ValueError(f"Application ID {i.application_id} is already in the list")
            app_ids.append(i.application_id)
        self.applications = applications
        self._applications_by_id = {i.application_id: i for i in applications}
        self.diameter_config = diameter_config
        self._avps = dict()
        self.ip_queue = IpQueue(framed_ip_address_cidr)
        if not session_manager:
            session_manager = SessionManager()
        if not subscribers:
            subscribers = Subscribers()
        self.session_manager = session_manager
        self.subscribers = subscribers
        self.set_session_manager(session_manager)
        self.set_subscribers(subscribers)
        for i in self.applications:
            for j in self.applications:
                if i.application_id != j.application_id:
                    i.related_apps.append(j)

        self.logger = logging.getLogger("diameter_telecom")
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

    def create_session(self, app_id: int, subscriber: Subscriber):
        app = self._applications_by_id.get(app_id)
        if not app:
            raise ValueError(f"Application ID {app_id} not found")
        if not hasattr(app, "create_session"):
            raise ValueError(f"Application {app_id} does not have a create_session method")
        return app.create_session(subscriber)

    def start_session(self, app_id: int, session: DiameterSession):
        app = self._applications_by_id.get(app_id)
        if not app:
            raise ValueError(f"Application ID {app_id} not found")
        if not hasattr(app, "create_request"):
            raise ValueError(f"Application {app_id} does not have a create_request method")
        request: Message = app.create_request(app.MESSAGE_CREATE_SESSION, session)
        # avps = self._avps.get(app_id, {})
        # destination_realm = self.diameter_config.get("destination_realm", app.node.realm_name)
        # request.destination_realm = destination_realm.encode()
        for key, value in self.get_avps(app_id).items():
            print(key, value)
            if hasattr(request, key):
                setattr(request, key, value)
        app.send_request_custom(request)

    def update_session(self, app_id: int, session: DiameterSession):
        app = self._applications_by_id.get(app_id)
        if not app:
            raise ValueError(f"Application ID {app_id} not found")
        if not hasattr(app, "create_request"):
            raise ValueError(f"Application {app_id} does not have a update_session method")
        request: Message = app.create_request(app.MESSAGE_UPDATE_SESSION, session)
        for key, value in self.get_avps(app_id).items():
            print(key, value)
            if hasattr(request, key):
                setattr(request, key, value)
        app.send_request_custom(request)

    def terminate_session(self, app_id: int, session: DiameterSession):
        app = self._applications_by_id.get(app_id)
        if not app:
            raise ValueError(f"Application ID {app_id} not found")
        if not hasattr(app, "create_request"):
            raise ValueError(f"Application {app_id} does not have a terminate_session method")
        request: Message = app.create_request(app.MESSAGE_TERMINATE_SESSION, session)
        for key, value in self.get_avps(app_id).items():
            print(key, value)
            if hasattr(request, key):
                setattr(request, key, value)
        app.send_request_custom(request)