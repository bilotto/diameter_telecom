from diameter.node.application import ThreadingApplication
from diameter.message import Message
from diameter.message.constants import *
import logging
from ..session_manager import SessionManager, Subscribers
from ..session import DiameterSession
from diameter_telecom.diameter.message import DiameterMessage
from typing import Dict
import time

class CommonThreadingApplication(ThreadingApplication):
    session_manager: SessionManager
    subscribers: Subscribers
    def __init__(self, application_id: int, is_acct_application: bool, is_auth_application: bool, max_threads: int = 1):
        super().__init__(application_id=application_id, is_acct_application=is_acct_application, is_auth_application=is_auth_application, max_threads=max_threads)
        self.session_manager = SessionManager()
        self.subscribers = Subscribers()
        self.logger = logging.getLogger("diameter_telecom.app")
        self._avps: Dict[str, str] = {}

    @property
    def avps(self):
        if self.is_auth_application:
            self._avps['auth_application_id'] = self.application_id
        if self.is_acct_application:
            self._avps['acct_application_id'] = self.application_id
        self._avps['origin_host'] = self.node.origin_host.encode()
        self._avps['origin_realm'] = self.node.realm_name.encode()
        self._avps['destination_realm'] = self.node.realm_name.encode()
        return self._avps

    def to_dict(self):
        app_dict = dict()
        app_dict['app_id'] = self.application_id
        app_dict['class'] = self.__class__.__name__
        app_dict['is_ready'] = self.is_ready.is_set()
        app_dict['node'] = self.node.origin_host
        app_dict['session_manager_id'] = self.session_manager.id
        app_dict['subscribers_id'] = self.subscribers.id
        return app_dict

    @property
    def _request_handler(self):
        return self.handle_request

    def __repr__(self):
        return f"{self.__class__.__name__}(application_id={self.application_id}, acc={self.is_acct_application}, auth={self.is_auth_application}, {self.node.origin_host})"
    
    def set_session_manager(self, session_manager: SessionManager):
        self.session_manager = session_manager

    def set_subscribers(self, subscribers: Subscribers):
        self.subscribers = subscribers

    def handle_request(self, message: Message):
        """Template method: processes request with owner tracking, delegates to subclass"""
        owner_id = f"{self.__class__.__name__}({self.node.origin_host})"
        
        # Process incoming request
        dm_request = DiameterMessage(message)
        self.session_manager.process_diameter_message(dm_request, owner=owner_id)
        
        # Delegate to subclass implementation
        answer = self._handle_request(message)
        
        # Process outgoing answer
        if answer:
            dm_answer = DiameterMessage(answer)
            self.session_manager.process_diameter_message(dm_answer, owner=owner_id)
        
        return answer

    def _handle_request(self, message: Message):
        """Override in subclasses to implement request handling logic"""
        raise NotImplementedError("Subclasses must implement _handle_request")

    def send_request_custom(self, diameter_message: DiameterMessage | Message, timeout=10):
        """Send request with full session management handled by SessionManager"""
        if isinstance(diameter_message, Message):
            diameter_message = DiameterMessage(diameter_message)
        if not diameter_message.timestamp:
            diameter_message.timestamp = time.time()
        self.logger.debug(f"Sending request {diameter_message.cmd_code} through node {self.node.origin_host}")
        self.logger.debug(f"{diameter_message.dump()}")
        
        owner_id = f"{self.__class__.__name__}({self.node.origin_host})"
        self.session_manager.process_diameter_message(diameter_message, owner=owner_id)
        answer = self.send_request(diameter_message.message, timeout)
        diameter_message_answer = DiameterMessage(answer)
        self.session_manager.process_diameter_message(diameter_message_answer, owner=owner_id)
        if not diameter_message_answer.timestamp:
            diameter_message_answer.timestamp = time.time()
        self.logger.debug(f"Received answer {diameter_message_answer.cmd_code} through node {self.node.origin_host}")
        self.logger.debug(f"{diameter_message_answer.dump()}")
        return diameter_message_answer