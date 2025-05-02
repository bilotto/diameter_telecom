from .custom_simple_threading_application import CustomSimpleThreadingApplication
from ..diameter_session import GxSession
from diameter.message.constants import APP_3GPP_GX
from ..diameter_message import DiameterMessage
from ..constants import *
import logging
from typing import Dict

logger = logging.getLogger(__name__)
class GxApplication(CustomSimpleThreadingApplication):
    def __init__(self, max_threads=1, request_handler=None):
        super().__init__(application_id=APP_3GPP_GX, is_acct_application=False, is_auth_application=True, max_threads=max_threads, request_handler=request_handler)
        self.sessions: Dict[str, GxSession] = {}

    def get_session_by_id(self, session_id: str) -> GxSession:
        return self.sessions.get(session_id)
    
    def add_session(self, session: GxSession):
        self.sessions[session.session_id] = session

    def send_request_custom(self, request: DiameterMessage, timeout=5):
        if not isinstance(request, DiameterMessage):
            raise ValueError("request must be an instance of DiameterMessage")
        session_id = request.session_id
        gx_session = self.get_session_by_id(session_id)
        if not gx_session:
            gx_session = GxSession(session_id)
            self.add_session(gx_session)
        gx_session.add_message(request)
        answer = super().send_request_custom(request)
        gx_session.add_message(answer)
        if not gx_session.active:
            self.remove_session(session_id)
        return answer