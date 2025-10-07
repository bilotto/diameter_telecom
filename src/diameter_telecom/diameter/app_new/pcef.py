from .common import CommonThreadingApplication
from diameter.message.constants import *
from diameter.message.commands import CreditControlRequest
# from diameter_telecom import GxSession, Subscriber
# from diameter_telecom.diameter.message import DiameterMessage, create_message
# from diameter_telecom.apn import ip_to_bytes
from diameter_telecom.diameter.constants import *
from diameter.message import Message
from typing import List
from ..message import DiameterMessage, create_message
from ..session.gx import GxSession
from .. import Subscriber

class PcefGxApplication(CommonThreadingApplication):
    MESSAGE_CREATE_SESSION = CCR_I
    MESSAGE_UPDATE_SESSION = CCR_U
    MESSAGE_TERMINATE_SESSION = CCR_T

    def __init__(self, max_threads: int = 1):
        super().__init__(application_id=APP_3GPP_GX, is_acct_application=False, is_auth_application=True, max_threads=max_threads)
        self.related_apps: List[CommonThreadingApplication] = []

    def handle_request(self, message: Message):
        pass

    def create_session(self, subscriber: Subscriber) -> GxSession:
        session_id = self.node.session_generator.next_id()
        gx_session = GxSession(session_id=session_id, subscriber=subscriber)
        # gx_session.framed_ip_address = self.ip_queue.get_ip()
        self.session_manager.sessions.add_session(APP_3GPP_GX, gx_session)
        return gx_session

    def create_request(self, message_name: str, session: GxSession) -> CreditControlRequest:
        request = CreditControlRequest()
        request.header.application_id = APP_3GPP_GX
        request.session_id = session.session_id
        for k, v in self.avps.items():
            setattr(request, k, v)
        request.service_context_id = "test"
        if message_name == CCR_I:
            request.cc_request_number = 0
            request.cc_request_type = E_CC_REQUEST_TYPE_INITIAL_REQUEST
        elif message_name == CCR_U:
            request.cc_request_number = session.cc_request_number + 1
            request.cc_request_type = E_CC_REQUEST_TYPE_UPDATE_REQUEST
        elif message_name == CCR_T:
            request.cc_request_number = 1
            request.cc_request_type = E_CC_REQUEST_TYPE_TERMINATION_REQUEST
        for key, value in session.avps.items():
            if hasattr(request, key):
                setattr(request, key, value)
        return request
