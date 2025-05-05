# from .ip_queue import APN
from ..diameter.message import DiameterMessage
from ..diameter.app import GxApplication, RxApplication
from ..diameter.constants import APP_3GPP_GX, APP_3GPP_RX
from ..diameter.session import GxSession, RxSession
import logging
logger = logging.getLogger(__name__)
import time

class VoiceService:
    def __init__(self, gx_app: GxApplication, rx_app: RxApplication):
        self.gx_app: GxApplication = gx_app
        self.rx_app: RxApplication = rx_app

    def send_request(self, request: DiameterMessage, timeout=5) -> DiameterMessage:
        request.timestamp = time.time()
        session_id = request.session_id
        answer = None
        if request.app_id == APP_3GPP_GX:
            gx_session = self.gx_app.get_session_by_id(session_id)
            if not gx_session:
                gx_session = GxSession(session_id)
                gx_session.add_message(request)
                self.gx_app.add_session(gx_session)
            logger.debug(f"Sending Gx request: {request}")
            answer: DiameterMessage = self.gx_app.send_request_custom(request, timeout)
        elif request.app_id == APP_3GPP_RX:
            print(f"Sending Rx request: {request}")
            rx_session = self.rx_app.get_session_by_id(session_id)
            if not rx_session:
                logger.debug(f"No rx_session found for session_id: {session_id}. Will create a new one")
                gx_session = None
                if request.message.framed_ip_address:
                    logger.debug(f"Request has framed_ip_address: {request.message.framed_ip_address}. Will try to find gx_session by framed_ip_address")
                    gx_session = self.gx_app.get_session_by_framed_ip_address(request.message.framed_ip_address)
                    if gx_session:
                        logger.debug(f"Found gx_session that rx_session is bind to: {gx_session}")
                        rx_session = RxSession(session_id, gx_session_id=gx_session.session_id, subscriber=gx_session.subscriber)
                    else:
                        logger.debug(f"No gx_session found for framed_ip_address: {request.message.framed_ip_address}. Will create a new rx_session")
                        rx_session = RxSession(session_id)
                    rx_session.add_message(request)
                    self.rx_app.add_session(rx_session)
            else:
                logger.info(f"Found rx_session: {rx_session}")
            logger.debug(f"Sending Rx request: {request}")
            answer: DiameterMessage = self.rx_app.send_request_custom(request, timeout)
        else:
            raise ValueError(f"Invalid app_id: {request.app_id}")
        logger.debug(f"Got answer: {answer}")
        return answer

    def start(self):
        if not self.gx_app.node._started:
            self.gx_app.node.start()
        if not self.rx_app.node._started:
            self.rx_app.node.start()
        self.gx_app.wait_for_ready()
        self.rx_app.wait_for_ready()

    def stop(self):
        if self.gx_app.node._started:
            self.gx_app.node.stop()
        if self.rx_app.node._started:
            self.rx_app.node.stop()

