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

    # Delegate session management to SessionManager
    def get_session_by_id(self, session_id: str) -> Optional[DiameterSession]:
        """Get session by ID using SessionManager"""
        return self.session_manager.get_session_by_id(self.application_id, session_id)
    
    def get_session_by_framed_ip(self, ip_address: str) -> Optional[DiameterSession]:
        """Get session by framed IP address using SessionManager"""
        return self.session_manager.get_session_by_framed_ip(self.application_id, ip_address)
    
    def get_session_by_framed_ipv6(self, ipv6_prefix: str) -> Optional[DiameterSession]:
        """Get session by framed IPv6 prefix using SessionManager"""
        return self.session_manager.get_session_by_framed_ipv6(self.application_id, ipv6_prefix)
    
    def get_session_by_msisdn(self, msisdn: str) -> Optional[DiameterSession]:
        """Get session by MSISDN using SessionManager"""
        return self.session_manager.get_session_by_msisdn(self.application_id, msisdn)

    def remove_session(self, session_id: str):
        """Remove session using SessionManager"""
        self.session_manager.remove_session(self.application_id, session_id)

    def add_subscriber(self, subscriber: Subscriber):
        """Add subscriber using SessionManager"""
        self.session_manager.add_subscriber(subscriber)
    
    def get_subscriber_by_msisdn(self, msisdn: str) -> Optional[Subscriber]:
        """Get subscriber by MSISDN using SessionManager"""
        return self.session_manager.get_subscriber_by_msisdn(msisdn)
    
    def get_subscriber_by_imsi(self, imsi: str) -> Optional[Subscriber]:
        """Get subscriber by IMSI using SessionManager"""
        return self.session_manager.get_subscriber_by_imsi(imsi)

    def send_request_custom(self, diameter_message: DiameterMessage, timeout=10):
        """Send request with full session management handled by SessionManager"""
        return self.session_manager.send_request_with_session_management(
            diameter_message, 
            self.send_request, 
            timeout
        )