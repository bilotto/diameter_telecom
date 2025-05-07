from typing import List, Dict, Callable, Optional
from ..diameter.helpers import Node
from ._entity import DiameterEntity
from ..diameter.handle_request import handle_request_gx
from ..subscriber import Subscriber
#
from ..diameter.constants import *
from diameter.message.commands import CreditControlRequest
from diameter_telecom.diameter.app import GxApplication

class PCEF(DiameterEntity):
    def __init__(self, origin_host: str, realm_name: str,
                 ip_addresses: List[str],
                 tcp_port: int = None, sctp_port: int = None,
                 vendor_ids: List[int] = None,
                 max_threads: int = 1,
                 request_handler: Callable = handle_request_gx):
        super().__init__(origin_host=origin_host, realm_name=realm_name, ip_addresses=ip_addresses, tcp_port=tcp_port, sctp_port=sctp_port, vendor_ids=vendor_ids)
        self.gx_app: GxApplication = GxApplication(max_threads=max_threads, request_handler=request_handler)

    # def start_gx_session(self, subscriber: Subscriber):
    #     """Start a Gx session for a subscriber"""
    #     ccr_i = CreditControlRequest()
    #     ccr_i.session_id = self.node.session_generator.next_id()
    #     ccr_i.cc_request_type = E_CC_REQUEST_TYPE_INITIAL_REQUEST
    #     ccr_i.cc_request_number = 0
    #     ccr_i.framed_ip_address = ip_to_bytes(self.framed_ip_address)
    #     ccr_i.subscription_id = subscriber.subscription_id()
