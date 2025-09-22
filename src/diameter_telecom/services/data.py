# from .ip_queue import APN
from ..diameter.message import DiameterMessage, create_message
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
from ..csv_file import CsvFile, write_to_csv
from .service import Service

@dataclass
class DataService(Service):
    pcef: PCEF
    ocs: OCS = None
    diameter_config: dict = None
    carrier: Carrier = None
    csv_file: CsvFile = None

    def __post_init__(self):
        super().__post_init__()
        
    def send_request(self, request: DiameterMessage, timeout=5) -> DiameterMessage:
        if not isinstance(request, DiameterMessage):
            raise TypeError("request must be an instance of DiameterMessage")
        
        request.timestamp = time.time()
        session_id = request.session_id
        logger.info(f"DataService sending {request.name} for session {session_id}")
        
        request = self.set_host_and_realm(request)
        
        if request.app_id == APP_3GPP_GX:
            logger.debug(f"Sending Gx request via PCEF {self.pcef.origin_host}")
            answer: DiameterMessage = self.gx_app.send_request_custom(request, timeout)
            logger.info(f"DataService received {answer.name} - Result: {getattr(answer.message, 'result_code', 'N/A')}")
        elif request.app_id == APP_3GPP_SY and self.ocs:
            logger.debug(f"Sending Sy request via OCS {self.ocs.origin_host}")
            answer: DiameterMessage = self.sy_app.send_request_custom(request, timeout)
            logger.info(f"DataService received Sy answer - Result: {getattr(answer.message, 'result_code', 'N/A')}")
        else:
            raise ValueError(f"DataService cannot handle app_id: {request.app_id}")
        
        logger.debug(f"DataService request-answer exchange completed for session {session_id}")
        return (request, answer)


    def start_gx_session(self, subscriber: Subscriber):
        ccr_i = create_message(CCR_I)
        ccr_i.header.application_id = APP_3GPP_GX
        ccr_i.auth_application_id = APP_3GPP_GX
        ccr_i.session_id = self.pcef.gx_app.node.session_generator.next_id()
        ccr_i.subscription_id = subscriber.subscription_id
        ccr_i.service_context_id = "test"
        if self.ip_queue:
            ccr_i.framed_ip_address = ip_to_bytes(self.ip_queue.get_ip())
            
        self.send_request(DiameterMessage(ccr_i))



# @dataclass
# class DataService:
#     pcef: PCEF
#     ocs: OCS = None
#     diameter_config: dict = None
#     carrier: Carrier = None
#     csv_file: CsvFile = None

#     def __post_init__(self):
#         if self.diameter_config is None:
#             self.diameter_config = {}
#             self.diameter_config[APP_3GPP_GX] = {}
#             if self.ocs:
#                 self.diameter_config[APP_3GPP_SY] = {}

#     @property
#     def gx_app(self):
#         return self.pcef.gx_app

#     @property
#     def sy_app(self):
#         if self.ocs:
#             return self.ocs.sy_app
        
#     def set_host_and_realm(self, diameter_message: DiameterMessage):
#         if diameter_message.app_id == APP_3GPP_GX:
#             diameter_message.message.origin_host = self.pcef.origin_host.encode()
#             diameter_message.message.origin_realm = (self.diameter_config[APP_3GPP_GX].get('origin_realm') or self.pcef.realm_name).encode()
#             diameter_message.message.destination_realm = (self.diameter_config[APP_3GPP_GX].get('destination_realm') or self.pcef.realm_name).encode()
#             if diameter_message.message.destination_host:
#                 diameter_message.message.destination_host = (self.diameter_config[APP_3GPP_GX].get('destination_host') or self.pcef.realm_name).encode()
#         else:
#             raise ValueError(f"Invalid app_id: {diameter_message.app_id}. Maybe missing to set the header?")
#         return diameter_message
    
#     def send_request(self, request: DiameterMessage, timeout=5) -> DiameterMessage:
#         if not isinstance(request, DiameterMessage):
#             raise TypeError("request must be an instance of DiameterMessage")
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
#             if self.csv_file:
#                 write_to_csv(self.csv_file, request)
#             answer: DiameterMessage = self.gx_app.send_request_custom(request, timeout)
#             if self.csv_file:
#                 write_to_csv(self.csv_file, answer)
#         else:
#             raise ValueError(f"Invalid app_id: {request.app_id}")
#         logger.debug(f"Got answer: {answer}")
#         return answer
    
#     def start(self):
#         if not self.gx_app.node._started:
#             self.gx_app.node.start()
#         if self.sy_app:
#             if not self.sy_app.node._started:
#                 self.sy_app.node.start()

#     def stop(self):
#         if self.gx_app.node._started:
#             self.gx_app.node.stop()
#         if self.sy_app:
#             if self.sy_app.node._started:
#                 self.sy_app.node.stop()


#     def wait_for_ready(self):
#         self.gx_app.wait_for_ready()
#         if self.sy_app:
#             self.sy_app.wait_for_ready()

