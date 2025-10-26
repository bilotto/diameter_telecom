from diameter.node.application import ThreadingApplication
from diameter.message import Message
from diameter.message.constants import *
import logging
from ..session_manager import SessionManager, Subscribers
from ..app_context import get_session_manager
from ..session_manager.sessions import Sessions
from ..message import DiameterMessage
from typing import Dict, Any
import time

class CommonThreadingApplication(ThreadingApplication):
    session_manager: SessionManager
    subscribers: Subscribers
    def __init__(self, application_id: int, is_acct_application: bool, is_auth_application: bool, max_threads: int = 1):
        super().__init__(application_id=application_id, is_acct_application=is_acct_application, is_auth_application=is_auth_application, max_threads=max_threads)
        # Use shared SessionManager from AppContext by default
        self.session_manager = get_session_manager()
        self.subscribers = self.session_manager.subscribers
        # Register as owner of the session manager
        self.session_manager.register_owner(self)
        self.logger = logging.getLogger("diameter_telecom.app")
        self._avps: Dict[str, str] = {}

    @property
    def sessions(self) -> Sessions:
        return self.session_manager.sessions

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
        self.subscribers = session_manager.subscribers
        self.session_manager.register_owner(self)

    # def set_subscribers(self, subscribers: Subscribers):
    #     # Delegate to session manager to keep single source of truth
    #     if hasattr(self.session_manager, 'set_subscribers'):
    #         self.session_manager.set_subscribers(subscribers)
    #     self.subscribers = self.session_manager.subscribers

    # Owner-based discovery of peer applications
    def get_app_by_id(self, app_id: int):
        """Lookup a peer application by app_id via SessionManager owners."""
        owners = self.session_manager.get_owners_by_app_id(app_id)
        # Prefer a different instance than self if multiple are registered
        for owner in owners:
            if owner is not self:
                return owner
        return owners[0] if owners else None

    def handle_request(self, message: Message):
        """Template method: processes request with owner tracking, delegates to subclass"""
        # Process incoming request
        dm_request = DiameterMessage(message)
        self.logger.info(f"Received request {dm_request.cmd_code} through node {self.node.origin_host}")
        self.logger.debug(f"\n{dm_request.dump()}")
        self.session_manager.process_diameter_message(dm_request, owner_app=self)
        # Delegate to subclass implementation
        answer = self._handle_request(message)
        
        # Process outgoing answer
        if answer:
            dm_answer = DiameterMessage(answer)
            self.session_manager.process_diameter_message(dm_answer, owner_app=self)
        
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
        self.logger.info(f"Sending request {diameter_message.cmd_code} through node {self.node.origin_host}")
        self.logger.debug(f"\n{diameter_message.dump()}")
        message = diameter_message.message
        if not message.header.end_to_end_identifier:  # Only if 0 (default)
            message.header.end_to_end_identifier = self.node.end_to_end_seq.next_sequence()
        self.session_manager.process_diameter_message(diameter_message, owner_app=self)
        answer = self.send_request(diameter_message.message, timeout)
        diameter_message_answer = DiameterMessage(answer)
        self.session_manager.process_diameter_message(diameter_message_answer, owner_app=self)
        if not diameter_message_answer.timestamp:
            diameter_message_answer.timestamp = time.time()
        self.logger.info(f"Received answer {diameter_message_answer.cmd_code} through node {self.node.origin_host}")
        self.logger.debug(f"\n{diameter_message_answer.dump()}")
        return diameter_message_answer