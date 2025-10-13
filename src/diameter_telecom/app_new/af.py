from typing import List

from diameter.message import Message
from diameter.message.commands.aa import AaRequest
from diameter.message.commands import SessionTerminationRequest

from .. import Subscriber
from ..constants import AAR, STR, APP_3GPP_RX
from ..message import DiameterMessage, create_message
from ..session.rx import RxSession
from .common import CommonThreadingApplication

class AfRxApplication(CommonThreadingApplication):
    MESSAGE_CREATE_SESSION = AAR
    MESSAGE_UPDATE_SESSION = AAR
    MESSAGE_TERMINATE_SESSION = STR

    def __init__(self, max_threads: int = 1):
        super().__init__(application_id=APP_3GPP_RX, is_acct_application=False, is_auth_application=True, max_threads=max_threads)
        self.related_apps: List[CommonThreadingApplication] = []

    def _handle_request(self, message: Message):
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
        request.header.application_id = APP_3GPP_RX
        for k, v in self.avps.items():
            setattr(request, k, v)
        request.session_id = session.session_id
        for key, value in session.avps.items():
            if hasattr(request, key):
                setattr(request, key, value)
        return request