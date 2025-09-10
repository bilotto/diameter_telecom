from diameter.node.application import SimpleThreadingApplication
from ..message import DiameterMessage
from ..session._diameter_session import DiameterSession
from ..constants import *
from .. import Subscriber
from typing import Dict, Optional
import logging
logger = logging.getLogger(__name__)
from ..session_manager import SessionManager

class CustomSimpleThreadingApplication(SimpleThreadingApplication):
    def __init__(self, application_id,
                 is_acct_application,
                 is_auth_application,
                 max_threads,
                 request_handler,
                 session_manager: SessionManager = None,
                 ):
        super().__init__(application_id, is_acct_application, is_auth_application, max_threads, request_handler)
        self.session_manager = session_manager if session_manager else SessionManager()

    def set_session_manager(self, session_manager: SessionManager):
        self.session_manager = session_manager

    # Note: Session and subscriber management methods are available directly through:
    # - self.session_manager.sessions.* for session operations
    # - self.session_manager.subscribers.* for subscriber operations

    def send_request_custom(self, diameter_message: DiameterMessage, timeout=10):
        """Send request with full session management handled by SessionManager"""
        return self.session_manager.send_request_with_session_management(
            diameter_message, 
            self.send_request, 
            timeout
        )