from .custom_simple_threading_application import CustomSimpleThreadingApplication
from ..session import RxSession
from ..constants import *
from ..message import DiameterMessage
from typing import List, Dict
from diameter.message.commands import SessionTerminationRequest
import logging
logger = logging.getLogger(__name__)

class RxApplication(CustomSimpleThreadingApplication):
    def __init__(self, max_threads=1, request_handler=None):
        super().__init__(application_id=APP_3GPP_RX, is_acct_application=False, is_auth_application=True, max_threads=max_threads, request_handler=request_handler)
        self.sessions: Dict[str, RxSession] = {}

    def get_session_by_id(self, session_id: str) -> RxSession:
        return self.sessions.get(session_id)

    def remove_session(self, session_id):
        logger.info(f"Removing Rx session {session_id}")
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def add_session(self, session: RxSession):
        self.sessions[session.session_id] = session

    def get_active_sessions(self) -> List[RxSession]:
        active_sessions = []
        for session in self.sessions.values():
            if session.active:
                active_sessions.append(session)
        return active_sessions
    

    def send_request_custom(self, request: DiameterMessage, timeout=5):
        if not isinstance(request, DiameterMessage):
            raise ValueError("request must be an instance of DiameterMessage")
        session_id = request.session_id
        rx_session = self.get_session_by_id(session_id)
        if not rx_session:
            rx_session = RxSession(session_id)
            # Add message before adding session so it's parsed properly by the add_message method
            rx_session.add_message(request)
            self.add_session(rx_session)
            if rx_session.subscriber:
                self.add_subscriber(rx_session.subscriber)
        else:
            rx_session.add_message(request)
        answer = super().send_request_custom(request)
        rx_session.add_message(answer)
        if not rx_session.active:
            self.remove_session(session_id)
        return answer
    
    def terminate_session_after_successful_abort(self, session_id: str):
        rx_session = self.get_session_by_id(session_id)
        if not rx_session:
            return
        last_message = rx_session.messages[-1]
        if last_message.name == ASA and last_message.result_code == E_RESULT_CODE_DIAMETER_SUCCESS:
            # Need to send STR
            # str_message = create_str_message(session_id)
            session_termination_request = SessionTerminationRequest()
            session_termination_request.header.is_proxyable = True
            session_termination_request.session_id = session_id
            session_termination_request.origin_host = last_message.origin_host
            session_termination_request.origin_realm = last_message.origin_realm
            session_termination_request.destination_realm = last_message.destination_realm
            session_termination_request.destination_host = last_message.destination_host
            session_termination_request.termination_cause = E_TERMINATION_CAUSE_DIAMETER_ADMINISTRATIVE
            str_message = DiameterMessage(session_termination_request)
            answer = self.send_request_custom(str_message)
