from .custom_simple_threading_application import CustomSimpleThreadingApplication
from ..session import RxSession
from ..constants import *
from ..message import DiameterMessage
from typing import List, Optional, Dict
from diameter.message.commands import SessionTerminationRequest
import logging
logger = logging.getLogger(__name__)

class RxApplication(CustomSimpleThreadingApplication):
    def __init__(self, max_threads=1, request_handler=None):
        super().__init__(application_id=APP_3GPP_RX, is_acct_application=False, is_auth_application=True, max_threads=max_threads, request_handler=request_handler)

    @property
    def sessions(self) -> Dict[str, RxSession]:
        return self.session_manager.sessions.get(APP_3GPP_RX, {})

    # Convenience methods for Rx-specific session lookups
    def get_rx_session_by_id(self, session_id: str) -> Optional[RxSession]:
        """Get Rx session by ID"""
        session = self.get_session_by_id(session_id)
        return session if isinstance(session, RxSession) else None

    def get_active_sessions(self) -> List[RxSession]:
        """Get all active Rx sessions"""
        active_sessions = []
        for session in self.session_manager.sessions.get(APP_3GPP_RX, {}).values():
            if isinstance(session, RxSession) and session.active:
                active_sessions.append(session)
        return active_sessions

    def send_request_custom(self, request: DiameterMessage, timeout=5):
        """Send request with session management handled by SessionManager"""
        if not isinstance(request, DiameterMessage):
            raise ValueError("request must be an instance of DiameterMessage")
        
        # All session management is now handled by SessionManager
        answer = super().send_request_custom(request, timeout)
        
        # Check if session should be removed after processing
        # session = self.get_rx_session_by_id(request.session_id)
        # if session and not session.active:
        #     logger.info(f"Removing Rx session {request.session_id}")
        #     self.remove_session(request.session_id)
        
        return answer
    
    def terminate_session_after_successful_abort(self, session_id: str):
        """Terminate session after successful abort"""
        rx_session = self.get_rx_session_by_id(session_id)
        if not rx_session:
            return
        last_message = rx_session.messages[-1]
        if last_message.name == ASA and last_message.result_code == E_RESULT_CODE_DIAMETER_SUCCESS:
            # Need to send STR
            session_termination_request = SessionTerminationRequest()
            session_termination_request.header.is_proxyable = True
            session_termination_request.header.application_id = APP_3GPP_RX
            session_termination_request.session_id = session_id
            session_termination_request.origin_host = last_message.origin_host
            session_termination_request.origin_realm = last_message.origin_realm
            session_termination_request.destination_realm = last_message.destination_realm
            session_termination_request.destination_host = last_message.destination_host
            session_termination_request.termination_cause = E_TERMINATION_CAUSE_DIAMETER_ADMINISTRATIVE
            str_message = DiameterMessage(session_termination_request)
            answer = self.send_request_custom(str_message)
