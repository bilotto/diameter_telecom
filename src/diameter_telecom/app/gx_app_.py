from .custom_simple_threading_application import CustomSimpleThreadingApplication
from ..diameter_session import GxSession
from diameter.message.constants import APP_3GPP_GX
from ..diameter_message import DiameterMessage

class GxApplication(CustomSimpleThreadingApplication):
    def __init__(self, max_threads=1, request_handler=None):
        super().__init__(application_id=APP_3GPP_GX, is_acct_application=False, is_auth_application=True, max_threads=max_threads, request_handler=request_handler)

    def get_session_by_id(self, session_id: str) -> GxSession:
        return self.sessions.get_session(session_id)
    
    def add_session(self, session: GxSession):
        self.sessions[session.session_id] = session

    def send_request_custom(self, request, timeout=5):
        if not isinstance(request, DiameterMessage):
            raise ValueError("request must be an instance of DiameterMessage")
        return self.send_request(request.message, timeout=timeout)