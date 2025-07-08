# from .ip_queue import APN
from ..diameter.message import DiameterMessage
from ..entities_3gpp import PCEF, AF
from ..diameter.constants import APP_3GPP_GX, APP_3GPP_RX
from ..diameter.session import GxSession, RxSession
import logging
logger = logging.getLogger(__name__)
import time
from ..carrier import Carrier
from .service import Service
from dataclasses import dataclass

@dataclass
class VoiceService(Service):
    pcef: PCEF
    af: AF = None
    diameter_config: dict = None
    carrier: Carrier = None

    def __post_init__(self):
        super().__post_init__()

    def send_request(self, request: DiameterMessage, timeout=5) -> DiameterMessage:
        logger.debug(f"Sending request: {request}")
        request.timestamp = time.time()
        session_id = request.session_id
        answer = None
        request = self.set_host_and_realm(request)
        if request.app_id == APP_3GPP_GX:
            gx_session = self.gx_app.get_session_by_id(session_id)
            if not gx_session:
                gx_session = GxSession(session_id)
                gx_session.add_message(request)
                self.gx_app.add_session(gx_session)
            logger.debug(f"Sending Gx request: {request}")
            answer: DiameterMessage = self.gx_app.send_request_custom(request, timeout)
        elif request.app_id == APP_3GPP_RX:
            rx_session = self.rx_app.get_session_by_id(session_id)
            #
            if not rx_session:
                logger.debug(f"No rx_session found for session_id: {session_id}. Will create a new one")
                gx_session = None
                if request.message.framed_ip_address:
                    gx_session = self.gx_app.get_session_by_framed_ip_address(request.message.framed_ip_address)
                    if gx_session:
                        logger.debug(f"Found gx_session that rx_session is bind to: {gx_session}")
                        rx_session = RxSession(session_id, gx_session_id=gx_session.session_id, subscriber=gx_session.subscriber)
                    rx_session.add_message(request)
                    self.rx_app.add_session(rx_session)
            #
            
            answer: DiameterMessage = self.rx_app.send_request_custom(request, timeout)
        else:
            raise ValueError(f"Invalid app_id: {request.app_id}")
        logger.debug(f"Got answer: {answer}")
        return answer


# class VoiceService:
#     def __init__(self, pcef: PCEF, af: AF, diameter_config: dict = None):
#         self.pcef: PCEF = pcef
#         self.af: AF = af
#         self.diameter_config = diameter_config
#         self.carrier: Carrier = None
#         logger.debug(f"VoiceService initialized with PCEF: {pcef}, AF: {af}, Diameter Config: {diameter_config}")

#     def __post_init__(self):
#         if self.diameter_config is None:
#             self.diameter_config = {}
#             self.diameter_config[APP_3GPP_GX] = {}
#             if self.ocs:
#                 self.diameter_config[APP_3GPP_RX] = {}


#     @property
#     def gx_app(self):
#         return self.pcef.gx_app

#     @property
#     def rx_app(self):
#         return self.af.rx_app
    
#     def set_host_and_realm(self, diameter_message: DiameterMessage):
#         if diameter_message.app_id == APP_3GPP_GX:
#             diameter_message.message.origin_host = self.pcef.origin_host.encode()
#             diameter_message.message.origin_realm = (self.diameter_config[APP_3GPP_GX].get('origin_realm') or self.pcef.realm_name).encode()
#             diameter_message.message.destination_realm = (self.diameter_config[APP_3GPP_GX].get('destination_realm') or self.pcef.realm_name).encode()
#             # diameter_message.message.destination_host = (self.diameter_config[APP_3GPP_GX].get('destination_host') or self.pcef.realm_name).encode()
#         elif diameter_message.app_id == APP_3GPP_RX:
#             diameter_message.message.origin_host = self.af.origin_host.encode()
#             diameter_message.message.origin_realm = (self.diameter_config[APP_3GPP_RX].get('origin_realm') or self.af.realm_name).encode()
#             diameter_message.message.destination_realm = (self.diameter_config[APP_3GPP_RX].get('destination_realm') or self.af.realm_name).encode()
#             # diameter_message.message.destination_host = (self.diameter_config[APP_3GPP_RX].get('destination_host') or self.pcef.realm_name).encode()
#         else:
#             raise ValueError(f"Invalid app_id: {diameter_message.app_id}. Maybe missing to set the header?")
#         return diameter_message


#     def send_request(self, request: DiameterMessage, timeout=5) -> DiameterMessage:
#         logger.debug(f"Sending request: {request}")
#         request.timestamp = time.time()
#         session_id = request.session_id
#         answer = None
#         request = self.set_host_and_realm(request)
#         if request.app_id == APP_3GPP_GX:
#             gx_session = self.gx_app.get_session_by_id(session_id)
#             if not gx_session:
#                 gx_session = GxSession(session_id)
#                 gx_session.add_message(request)
#                 self.gx_app.add_session(gx_session)
#             logger.debug(f"Sending Gx request: {request}")
#             answer: DiameterMessage = self.gx_app.send_request_custom(request, timeout)
#         elif request.app_id == APP_3GPP_RX:
#             rx_session = self.rx_app.get_session_by_id(session_id)
#             #
#             if not rx_session:
#                 logger.debug(f"No rx_session found for session_id: {session_id}. Will create a new one")
#                 gx_session = None
#                 if request.message.framed_ip_address:
#                     gx_session = self.gx_app.get_session_by_framed_ip_address(request.message.framed_ip_address)
#                     if gx_session:
#                         logger.debug(f"Found gx_session that rx_session is bind to: {gx_session}")
#                         rx_session = RxSession(session_id, gx_session_id=gx_session.session_id, subscriber=gx_session.subscriber)
#                     rx_session.add_message(request)
#                     self.rx_app.add_session(rx_session)
#             #
            
#             answer: DiameterMessage = self.rx_app.send_request_custom(request, timeout)
#         else:
#             raise ValueError(f"Invalid app_id: {request.app_id}")
#         logger.debug(f"Got answer: {answer}")
#         return answer

#     def start(self):
#         if not self.gx_app.node._started:
#             self.gx_app.node.start()
#         if not self.rx_app.node._started:
#             self.rx_app.node.start()
#         # self.gx_app.wait_for_ready()
#         # self.rx_app.wait_for_ready()

#     def stop(self):
#         if self.gx_app.node._started:
#             self.gx_app.node.stop()
#         if self.rx_app.node._started:
#             self.rx_app.node.stop()


#     def wait_for_ready(self):
#         self.gx_app.wait_for_ready()
#         self.rx_app.wait_for_ready()

