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
        answer = None
        request = self.set_host_and_realm(request)
        if request.app_id == APP_3GPP_GX:
            gx_session = self.gx_app.get_session_by_id(session_id)
            if not gx_session:
                gx_session = GxSession(session_id)
                gx_session.add_message(request)
                self.gx_app.add_session(gx_session)
            logger.debug(f"Sending Gx request: {request}")
            if self.csv_file:
                write_to_csv(self.csv_file, request)
            answer: DiameterMessage = self.gx_app.send_request_custom(request, timeout)
            if self.csv_file:
                write_to_csv(self.csv_file, answer)
        else:
            raise ValueError(f"Invalid app_id: {request.app_id}")
        logger.debug(f"Got answer: {answer}")
        return (request, answer)


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

