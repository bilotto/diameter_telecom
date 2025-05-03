from .custom_simple_threading_application import CustomSimpleThreadingApplication
from ..session import GxSession
from diameter.message.constants import APP_3GPP_GX
from ..message import DiameterMessage
from ..constants import *
import logging
from typing import Dict

logger = logging.getLogger(__name__)
class GxApplication(CustomSimpleThreadingApplication):
    def __init__(self, max_threads=1, request_handler=None):
        super().__init__(application_id=APP_3GPP_GX, is_acct_application=False, is_auth_application=True, max_threads=max_threads, request_handler=request_handler)
        self.sessions: Dict[str, GxSession] = {}
        self.sessions_id_by_framed_ip_address: Dict[str, str] = {}
        self.sessions_id_by_framed_ipv6_prefix: Dict[str, str] = {}

    def get_session_by_id(self, session_id: str) -> GxSession:
        return self.sessions.get(session_id)
    
    def add_session(self, session: GxSession):
        self.sessions[session.session_id] = session
        if session.framed_ip_address:
            self.sessions_id_by_framed_ip_address[session.framed_ip_address] = session.session_id
        if session.framed_ipv6_prefix:
            self.sessions_id_by_framed_ipv6_prefix[session.framed_ipv6_prefix] = session.session_id

    def remove_session(self, session_id: str):
        session = self.sessions.pop(session_id)
        if session.framed_ip_address:
            self.sessions_id_by_framed_ip_address.pop(session.framed_ip_address)
        if session.framed_ipv6_prefix:
            self.sessions_id_by_framed_ipv6_prefix.pop(session.framed_ipv6_prefix)
            
    def send_request_custom(self, request: DiameterMessage, timeout=5):
        if not isinstance(request, DiameterMessage):
            raise ValueError("request must be an instance of DiameterMessage")
        session_id = request.session_id
        gx_session = self.get_session_by_id(session_id)
        if not gx_session:
            gx_session = GxSession(session_id)
            gx_session.add_message(request)
            self.add_session(gx_session)
        #
        #
        answer = super().send_request_custom(request, timeout)
        gx_session.add_message(answer)
        if not gx_session.active:
            self.remove_session(session_id)
        return answer