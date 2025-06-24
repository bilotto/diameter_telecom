# from .ip_queue import APN
from ..diameter.message import DiameterMessage
from ..entities_3gpp import PCEF, OCS
from ..diameter.constants import *
from ..diameter.session import GxSession, SySession
from ..subscriber import Subscriber
import logging
logger = logging.getLogger(__name__)
import time
from ..apn import *
from ..carrier import Carrier
from dataclasses import dataclass

@dataclass
class DataService:
    pcef: PCEF
    ocs: OCS = None
    diameter_config: dict = None
    carrier: Carrier = None

    @property
    def gx_app(self):
        return self.pcef.gx_app

    @property
    def sy_app(self):
        if self.ocs:
            return self.ocs.sy_app
    
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
        else:
            raise ValueError(f"Invalid app_id: {request.app_id}")
        logger.debug(f"Got answer: {answer}")
        return answer
    
    def start(self):
        if not self.gx_app.node._started:
            self.gx_app.node.start()
        if self.sy_app:
            if not self.sy_app.node._started:
                self.sy_app.node.start()

    def stop(self):
        if self.gx_app.node._started:
            self.gx_app.node.stop()
        if self.sy_app:
            if self.sy_app.node._started:
                self.sy_app.node.stop()


    def wait_for_ready(self):
        self.gx_app.wait_for_ready()
        if self.sy_app:
            self.sy_app.wait_for_ready()

