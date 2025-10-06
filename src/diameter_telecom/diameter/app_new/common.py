from diameter.node.application import ThreadingApplication
from diameter.message import Message
from diameter.message.constants import *
import logging
from ..session_manager import SessionManager, Subscribers
from ..session import DiameterSession
from diameter_telecom.diameter.message import DiameterMessage
from typing import Dict


class CommonThreadingApplication(ThreadingApplication):
    session_manager: SessionManager
    subscribers: Subscribers
    def __init__(self, application_id: int, is_acct_application: bool, is_auth_application: bool, max_threads: int = 1):
        super().__init__(application_id=application_id, is_acct_application=is_acct_application, is_auth_application=is_auth_application, max_threads=max_threads)
        self.session_manager = SessionManager()
        self.subscribers = Subscribers()
        self.logger = logging.getLogger("diameter_telecom")
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
        pass

    def send_request_custom(self, diameter_message: DiameterMessage | Message, timeout=10):
        """Send request with full session management handled by SessionManager"""
        if isinstance(diameter_message, Message):
            diameter_message = DiameterMessage(diameter_message)
        self.logger.debug(f"Sending request {diameter_message.cmd_code} through node {self.node.origin_host}")
        self.logger.debug(f"{diameter_message.dump()}")
        answer = self.session_manager.send_request_with_session_management(
            diameter_message, 
            self.send_request, 
            timeout
        )
        self.logger.debug(f"Received answer {answer.cmd_code} through node {self.node.origin_host}")
        self.logger.debug(f"{answer.dump()}")
        return answer