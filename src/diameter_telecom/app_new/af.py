from typing import List

from diameter.message import Message
from diameter.message.commands.aa import AaRequest
from diameter.message.commands import SessionTerminationRequest, ReAuthRequest, ReAuthAnswer, AbortSessionRequest, AbortSessionAnswer, SessionTerminationAnswer
# from diameter.node.node import AbortSessionRequest

from .. import Subscriber
from ..constants import *
from ..message import DiameterMessage
from ..session.rx import RxSession
from .common import CommonThreadingApplication

class AfRxApplication(CommonThreadingApplication):
    MESSAGE_CREATE_SESSION = AAR
    MESSAGE_UPDATE_SESSION = AAR
    MESSAGE_TERMINATE_SESSION = STR
    MESSAGE_ABORT_SESSION = ASR

    def __init__(self, max_threads: int = 1):
        super().__init__(application_id=APP_3GPP_RX, is_acct_application=False, is_auth_application=True, max_threads=max_threads)
        # related_apps removed; use owner-based discovery via get_app_by_id

    def _handle_request(self, message: Message):
        self.logger.info(f"{__class__.__name__} Received request {message.header.command_code} through node {self.node.origin_host}")
        session: RxSession = self.session_manager.sessions.get_rx_session(message.session_id)
        if not session:
            self.logger.error(f"Session {message.session_id} not found")
            return None
        if isinstance(message, ReAuthRequest):
            answer = ReAuthAnswer()
            answer.session_id = message.session_id
            answer.origin_host = self.node.origin_host.encode()
            answer.origin_realm = self.node.realm_name.encode()
            answer.destination_realm = message.origin_realm
            answer.destination_host = message.origin_host
            answer.auth_application_id = APP_3GPP_RX
            answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
            return answer
        elif isinstance(message, AbortSessionRequest):
            answer: AbortSessionAnswer = message.to_answer()
            answer.session_id = message.session_id
            answer.origin_host = self.node.origin_host.encode()
            answer.origin_realm = self.node.realm_name.encode()
            answer.destination_realm = message.origin_realm
            answer.destination_host = message.origin_host
            answer.auth_application_id = APP_3GPP_RX
            answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
            # Need to init the abort attribute
            session.abort = True
            return answer

    def create_session(self, subscriber: Subscriber) -> RxSession:
        session_id = self.node.session_generator.next_id()
        rx_session = RxSession(session_id=session_id, subscriber=subscriber)
        # self.session_manager.sessions.add_rx_session(rx_session)
        subscriber.add_session_id(APP_3GPP_RX, session_id)
        return rx_session

    def create_request(self, message_name: str, session: RxSession) -> AaRequest | SessionTerminationRequest:
        if message_name == AAR:
            request = AaRequest()
        elif message_name == STR:
            request = SessionTerminationRequest()
            request.termination_cause = E_TERMINATION_CAUSE_DIAMETER_LOGOUT
        request.header.application_id = APP_3GPP_RX
        request.session_id = session.session_id
        return request