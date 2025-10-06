from diameter.message.commands.aa import AaRequest


from .common import CommonThreadingApplication
from diameter.message.constants import *
from diameter.message.commands import AaRequest, SessionTerminationRequest
# from diameter_telecom import GxSession, Subscriber
# from diameter_telecom.diameter.message import DiameterMessage, create_message
# from diameter_telecom.apn import ip_to_bytes
from diameter_telecom.diameter.constants import *
from diameter.message import Message
from typing import List
from ..message import DiameterMessage, create_message
from ..session.rx import RxSession
from .. import Subscriber

class AfRxApplication(CommonThreadingApplication):
    MESSAGE_CREATE_SESSION = AAR
    MESSAGE_UPDATE_SESSION = AAR
    MESSAGE_TERMINATE_SESSION = STR

    def __init__(self, max_threads: int = 1):
        super().__init__(application_id=APP_3GPP_RX, is_acct_application=False, is_auth_application=True, max_threads=max_threads)
        self.related_apps: List[CommonThreadingApplication] = []

    def handle_request(self, message: Message):
        pass


    def create_session(self, subscriber: Subscriber) -> RxSession:
        session_id = self.node.session_generator.next_id()
        rx_session = RxSession(session_id=session_id, subscriber=subscriber)
        return rx_session

    def create_request(self, message_name: str, session: RxSession) -> AaRequest | SessionTerminationRequest:
        if message_name == AAR:
            request = AaRequest()
        elif message_name == STR:
            request = SessionTerminationRequest()
        return request