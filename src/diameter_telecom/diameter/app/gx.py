from .custom_simple_threading_application import CustomSimpleThreadingApplication
from ..session import GxSession
from diameter.message.constants import APP_3GPP_GX
from ..message import DiameterMessage
from ..constants import *
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class GxApplication(CustomSimpleThreadingApplication):
    def __init__(self, max_threads=1, request_handler=None):
        super().__init__(application_id=APP_3GPP_GX, is_acct_application=False, is_auth_application=True, max_threads=max_threads, request_handler=request_handler)

    @property
    def sessions(self) -> Dict[str, GxSession]:
        """Get all Gx sessions"""
        return self.session_manager.sessions.get(APP_3GPP_GX, {})

    # Convenience methods for Gx-specific session lookups
    def get_gx_session_by_id(self, session_id: str) -> Optional[GxSession]:
        """Get Gx session by ID"""
        session = self.get_session_by_id(session_id)
        return session if isinstance(session, GxSession) else None
    
    def get_gx_session_by_framed_ip_address(self, framed_ip_address: str) -> Optional[GxSession]:
        """Get Gx session by framed IP address"""
        session = self.get_session_by_framed_ip(framed_ip_address)
        return session if isinstance(session, GxSession) else None
    
    def get_gx_session_by_framed_ipv6_prefix(self, framed_ipv6_prefix: str) -> Optional[GxSession]:
        """Get Gx session by framed IPv6 prefix"""
        session = self.get_session_by_framed_ipv6(framed_ipv6_prefix)
        return session if isinstance(session, GxSession) else None
    
    def get_gx_session_by_msisdn(self, msisdn: str) -> Optional[GxSession]:
        """Get Gx session by MSISDN"""
        session = self.get_session_by_msisdn(msisdn)
        return session if isinstance(session, GxSession) else None

    def send_request_custom(self, request: DiameterMessage, timeout=5):
        """Send request with session management handled by SessionManager"""
        if not isinstance(request, DiameterMessage):
            raise ValueError("request must be an instance of DiameterMessage")
        
        # All session management is now handled by SessionManager
        answer = super().send_request_custom(request, timeout)
        
        # Check if session should be removed after processing
        # session = self.get_gx_session_by_id(request.session_id)
        # if session and not session.active:
        #     logger.debug(f"GxSession {request.session_id} is not active. Removing it.")
        #     self.remove_session(request.session_id)
        
        return answer