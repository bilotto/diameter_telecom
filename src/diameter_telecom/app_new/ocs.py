from typing import List

from diameter.message import Message
from diameter.message.commands import SpendingLimitRequest, SpendingStatusNotificationRequest, SessionTerminationRequest
from diameter.message.constants import *

from .. import Subscriber
from ..constants import *
from ..diameter_layer.parse_avp import *
from ..message import DiameterMessage, create_message
from ..session.sy import SySession
from .common import CommonThreadingApplication


class OcsSyApplication(CommonThreadingApplication):
    MESSAGE_CREATE_SESSION = None
    MESSAGE_UPDATE_SESSION = SSNR
    MESSAGE_TERMINATE_SESSION = None
    def __init__(self, max_threads: int = 1):
        super().__init__(application_id=APP_3GPP_SY, is_acct_application=False, is_auth_application=True, max_threads=max_threads)
        self.related_apps: List[CommonThreadingApplication] = []

    def _handle_request(self, message: SpendingLimitRequest | SpendingStatusNotificationRequest | SessionTerminationRequest):
        answer = message.to_answer()
        answer.session_id = message.session_id
        answer.origin_host = message.destination_host
        answer.origin_realm = message.destination_realm
        answer.destination_realm = message.destination_realm
        answer.destination_host = message.destination_host
        answer.auth_application_id = message.auth_application_id

        # Parameter check
        if not hasattr(message, "session_id") or not message.session_id:
            self.logger.error("❌ OCS Sy: Missing session_id in request")
            raise ValueError("Missing session_id in request")
        if not hasattr(message, "subscription_id") or not message.subscription_id:
            self.logger.error("❌ OCS Sy: Missing subscription_id in request")
            raise ValueError("Missing subscription_id in request")

        # Query node_manager/session_manager for session
        sy_session = self.session_manager.sessions.get_session_by_id(APP_3GPP_SY, message.session_id)
        if not sy_session:
            self.logger.error(f"❌ OCS Sy: Session {message.session_id} not found")
            raise ValueError(f"Session {message.session_id} not found")

        # Business logic for each message type
        if isinstance(message, SpendingLimitRequest):
            self.logger.info(f"💰 OCS Sy: Handling SpendingLimitRequest for session {message.session_id}")
            # Example: Always allow for demo
            answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
        elif isinstance(message, SpendingStatusNotificationRequest):
            self.logger.info(f"🔔 OCS Sy: Handling SpendingStatusNotificationRequest for session {message.session_id}")
            answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
        elif isinstance(message, SessionTerminationRequest):
            self.logger.info(f"🛑 OCS Sy: Handling SessionTerminationRequest for session {message.session_id}")
            answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
            sy_session.end()
        else:
            self.logger.warning(f"⚠️ OCS Sy: Unknown request type {type(message)} for session {message.session_id}")
            answer.result_code = E_RESULT_CODE_DIAMETER_UNABLE_TO_COMPLY

        return answer


    def create_session(self, subscriber: Subscriber) -> SySession:
        sy_session = SySession(self.node.session_generator.next_id(), subscriber=subscriber)
        self.session_manager.sessions.add_session(APP_3GPP_SY, sy_session)
        return sy_session

    def create_request(self, message_name: str, session: SySession) -> SpendingLimitRequest | SpendingStatusNotificationRequest | SessionTerminationRequest:
        if message_name == SLR:
            request = SpendingLimitRequest()
        elif message_name == SSNR:
            request = SpendingStatusNotificationRequest()
        elif message_name == STR:
            request = SessionTerminationRequest()
        return request