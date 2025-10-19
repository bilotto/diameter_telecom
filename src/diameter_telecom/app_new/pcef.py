from typing import List

from diameter.message import Message
from diameter.message.commands import CreditControlRequest, ReAuthRequest, ReAuthAnswer
from diameter.message.constants import *

from .. import Subscriber
from ..constants import CCR_I, CCR_U, CCR_T
from ..message import DiameterMessage, create_message
from ..session.gx import GxSession
from .common import CommonThreadingApplication

class PcefGxApplication(CommonThreadingApplication):
    MESSAGE_CREATE_SESSION = CCR_I
    MESSAGE_UPDATE_SESSION = CCR_U
    MESSAGE_TERMINATE_SESSION = CCR_T

    def __init__(self, max_threads: int = 1):
        super().__init__(application_id=APP_3GPP_GX, is_acct_application=False, is_auth_application=True, max_threads=max_threads)
        self.related_apps: List[CommonThreadingApplication] = []

    def _handle_request(self, message: Message):
        # Receives the RAR from PCRF
        answer: ReAuthAnswer = message.to_answer()
        answer.session_id = message.session_id
        answer.origin_host = self.node.origin_host.encode()
        answer.origin_realm = self.node.realm_name.encode()
        answer.destination_realm = message.origin_realm
        answer.destination_host = message.origin_host
        answer.auth_application_id = APP_3GPP_GX
        answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
        return answer

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
            self.logger.debug(f"First layer of AVPS (app.avps): {k} = {v}")
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
            self.logger.debug(f"Second layer of AVPS (session.avps): {key} = {value}")
            if hasattr(request, key):
                setattr(request, key, value)
        return request
