from .custom_simple_threading_application import CustomSimpleThreadingApplication
from ..diameter_session import SySession
from diameter.message.constants import APP_3GPP_SY
from ..diameter_message import DiameterMessage
from typing import Dict

class SyApplication(CustomSimpleThreadingApplication):
    def __init__(self, max_threads=1, request_handler=None):
        super().__init__(application_id=APP_3GPP_SY, is_acct_application=False, is_auth_application=True, max_threads=max_threads, request_handler=request_handler)
        self.sessions: Dict[str, SySession] = {}

    def get_session_by_id(self, session_id: str) -> SySession:
        return self.sessions.get(session_id)
    
    def add_session(self, session: SySession):
        self.sessions[session.session_id] = session

    def send_request_custom(self, request: DiameterMessage, timeout=5):
        if not isinstance(request, DiameterMessage):
            raise ValueError("request must be an instance of DiameterMessage")
        session_id = request.session_id
        sy_session = self.get_session_by_id(session_id)
        if not sy_session:
            sy_session = SySession(session_id)
            self.add_session(sy_session)
        sy_session.add_message(request)


