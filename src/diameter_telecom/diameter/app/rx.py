from .custom_simple_threading_application import CustomSimpleThreadingApplication
from ..session import RxSession
from ..constants import APP_3GPP_RX
from ..message import DiameterMessage
from typing import List, Dict

class RxApplication(CustomSimpleThreadingApplication):
    def __init__(self, max_threads=1, request_handler=None):
        super().__init__(application_id=APP_3GPP_RX, is_acct_application=False, is_auth_application=True, max_threads=max_threads, request_handler=request_handler)
        self.sessions: Dict[str, RxSession] = {}

    def get_session_by_id(self, session_id: str) -> RxSession:
        return self.sessions.get(session_id)
    
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