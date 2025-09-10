from .custom_simple_threading_application import CustomSimpleThreadingApplication
from ..session import SySession
from ..constants import APP_3GPP_SY
from ..message import DiameterMessage
from typing import Optional, Dict

class SyApplication(CustomSimpleThreadingApplication):
    def __init__(self, max_threads=1, request_handler=None):
        super().__init__(application_id=APP_3GPP_SY, is_acct_application=False, is_auth_application=True, max_threads=max_threads, request_handler=request_handler)

    @property
    def sessions(self) -> Dict[str, SySession]:
        return self.session_manager.sessions.get(APP_3GPP_SY, {})

    # Convenience methods for Sy-specific session lookups
    def get_sy_session_by_id(self, session_id: str) -> Optional[SySession]:
        """Get Sy session by ID"""
        session = self.get_session_by_id(session_id)
        return session if isinstance(session, SySession) else None

    def send_request_custom(self, request: DiameterMessage, timeout=5):
        """Send request with session management handled by SessionManager"""
        if not isinstance(request, DiameterMessage):
            raise ValueError("request must be an instance of DiameterMessage")
        
        # All session management is now handled by SessionManager
        return super().send_request_custom(request, timeout)


