from typing import List

from diameter.message import Message
from diameter.message.commands import SpendingLimitRequest, SpendingStatusNotificationRequest, SessionTerminationRequest, SpendingLimitAnswer, SpendingStatusNotificationAnswer, SessionTerminationAnswer, AbortSessionRequest, AbortSessionAnswer
from diameter.message.constants import *

from diameter.message.avp.grouped import PolicyCounterStatusReport

from .. import Subscriber
from ..constants import *
from ..diameter_layer.parse_avp import *
from ..message import DiameterMessage
from ..session.sy import SySession
from .common import CommonThreadingApplication


class OcsSyApplication(CommonThreadingApplication):
    MESSAGE_CREATE_SESSION = None
    MESSAGE_UPDATE_SESSION = SSNR
    MESSAGE_TERMINATE_SESSION = None
    MESSAGE_ABORT_SESSION = None
    def __init__(self, max_threads: int = 1):
        super().__init__(application_id=APP_3GPP_SY, is_acct_application=False, is_auth_application=True, max_threads=max_threads)
        # related_apps removed; use owner-based discovery via get_app_by_id

    def _handle_request(self, message: SpendingLimitRequest | SessionTerminationRequest):
        answer = message.to_answer()
        answer.session_id = message.session_id
        answer.origin_host = message.destination_host
        answer.origin_realm = message.destination_realm
        answer.destination_realm = message.destination_realm
        answer.destination_host = message.destination_host
        answer.auth_application_id = message.auth_application_id

        sy_session = None

        # Parameter check
        if not hasattr(message, "session_id") or not message.session_id:
            self.logger.error("❌ OCS Sy: Missing session_id in request")
            raise ValueError("Missing session_id in request")
        if not hasattr(message, "subscription_id") or not message.subscription_id:
            self.logger.error("❌ OCS Sy: Missing subscription_id in request")
            raise ValueError("Missing subscription_id in request")

        # # Query node_manager/session_manager for session
        sy_session = self.session_manager.sessions.get_session_by_id(APP_3GPP_SY, message.session_id)
        if not sy_session:
            self.logger.error(f"❌ OCS Sy: Session {message.session_id} not found")
            # Check if is a STR (Session Termination Request). If so, let it pass so the session can be terminated on the other side even if does not exist in our session manager.
            if not isinstance(message, SessionTerminationRequest):
                raise ValueError(f"Session {message.session_id} not found")

        # Business logic for each message type
        if isinstance(message, SpendingLimitRequest):
            if not isinstance(answer, SpendingLimitAnswer):
                raise ValueError("Answer is not a SpendingLimitAnswer")
            self.logger.info(f"💰 OCS Sy: Handling SpendingLimitRequest for session {message.session_id}")
            msisdn = None
            imsi = None
            subscriber = None
            if message.subscription_id:
                msisdn, imsi, _, _, _ = parse_subscription_id(message.subscription_id)
            if msisdn:
                subscriber = self.subscribers.get_subscriber_by_msisdn(msisdn)
                self.logger.debug(f"👤 Gx CCR: Found subscriber by MSISDN: {subscriber}")
            elif imsi:
                subscriber = self.subscribers.get_subscriber_by_imsi(imsi)
                self.logger.debug(f"👤 Gx CCR: Found subscriber by IMSI: {imsi}")

            if not subscriber:
                answer.result_code = E_RESULT_CODE_DIAMETER_USER_UNKNOWN
            else:
                answer = subscriber.add_avps(answer)

            answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
        elif isinstance(message, SessionTerminationRequest):
            self.logger.info(f"🛑 OCS Sy: Handling SessionTerminationRequest for session {message.session_id}")
            answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
            if sy_session:
                sy_session.end()
        else:
            self.logger.warning(f"⚠️ OCS Sy: Unknown request type {type(message)} for session {message.session_id}")
            answer.result_code = E_RESULT_CODE_DIAMETER_UNABLE_TO_COMPLY

        # if not answer.origin_host:
        #     answer.origin_host = self.node.origin_host.encode()

        return answer


    def create_session(self, subscriber: Subscriber) -> SySession:
        sy_session = SySession(self.node.session_generator.next_id(), subscriber=subscriber)
        # self.session_manager.sessions.add_session(APP_3GPP_SY, sy_session)
        return sy_session

    def create_request(self, message_name: str, session: SySession) -> SpendingStatusNotificationRequest | AbortSessionRequest:
        if message_name == SSNR:
            request = SpendingStatusNotificationRequest()
        else:
            raise ValueError(f"Unknown message name: {message_name}")
        request.header.application_id = APP_3GPP_SY
        request.session_id = session.session_id
        return request