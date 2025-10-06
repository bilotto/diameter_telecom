from .common import CommonThreadingApplication
from diameter.message.constants import *
from diameter.message import Message
from diameter.message.commands import SpendingLimitRequest, SpendingStatusNotificationRequest, SessionTerminationRequest
from diameter.message.avp import *
from diameter.message.avp.grouped import *
from .. import Subscriber
# from diameter_telecom import GxSession, Subscriber
# from diameter_telecom.diameter.message import DiameterMessage, create_message
# from diameter_telecom.apn import ip_to_bytes
# from diameter_telecom.diameter.constants import *
# from diameter_telecom.diameter.parse_avp import *
from ..constants import *
from ..parse_avp import *
from ..message import DiameterMessage, create_message
from ..session.sy import SySession
from typing import List


class OcsSyApplication(CommonThreadingApplication):
    MESSAGE_CREATE_SESSION = SLR
    MESSAGE_UPDATE_SESSION = SSNR
    MESSAGE_TERMINATE_SESSION = STR
    def __init__(self, max_threads: int = 1):
        super().__init__(application_id=APP_3GPP_SY, is_acct_application=False, is_auth_application=True, max_threads=max_threads)
        self.related_apps: List[CommonThreadingApplication] = []

    def handle_request(self, message: Message):
        answer = message.to_answer()
        answer.cc_request_number = message.cc_request_number
        answer.cc_request_type = message.cc_request_type
        return answer

    def create_session(self, subscriber: Subscriber) -> SySession:
        sy_session = SySession(self.node.session_generator.next_id(), subscriber=subscriber)
        return sy_session

    def create_request(self, message_name: str, session: SySession) -> SpendingLimitRequest | SpendingStatusNotificationRequest | SessionTerminationRequest:
        if message_name == SLR:
            request = SpendingLimitRequest()
        elif message_name == SSNR:
            request = SpendingStatusNotificationRequest()
        elif message_name == STR:
            request = SessionTerminationRequest()
        return request