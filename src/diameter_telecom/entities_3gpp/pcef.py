from typing import List, Dict, Callable, Optional
from ..diameter.helpers import Node
from ._entity import DiameterEntity
from ..diameter.handle_request import handle_request_gx
from ..subscriber import Subscriber
#
from ..diameter.constants import *
from diameter.message.commands import CreditControlRequest
from diameter_telecom.diameter.app import GxApplication
from ..apn import APN, ip_to_bytes, bytes_to_ip

class PCEF(DiameterEntity):
    def __init__(self, origin_host: str, realm_name: str,
                 ip_addresses: List[str],
                 tcp_port: int = None, sctp_port: int = None,
                 vendor_ids: List[int] = None,
                 max_threads: int = 1,
                 request_handler: Callable = handle_request_gx):
        super().__init__(origin_host=origin_host, realm_name=realm_name, ip_addresses=ip_addresses, tcp_port=tcp_port, sctp_port=sctp_port, vendor_ids=vendor_ids)
        self.gx_app: GxApplication = GxApplication(max_threads=max_threads, request_handler=request_handler)

    def start_gx_session(self, subscriber: Subscriber):
        """Start a Gx session for a subscriber"""
        ccr_i = CreditControlRequest()
        ccr_i.auth_application_id = APP_3GPP_GX
        ccr_i.session_id = self.node.session_generator.next_id()
        ccr_i.origin_host = self.origin_host.encode()
        ccr_i.origin_realm = self.realm_name.encode()
        ccr_i.destination_realm = self.realm_name.encode()
        ccr_i.cc_request_type = E_CC_REQUEST_TYPE_INITIAL_REQUEST
        ccr_i.cc_request_number = 0
        ccr_i.framed_ip_address = ip_to_bytes(subscriber.apn.ip_queue.get_ip())
        ccr_i.subscription_id = subscriber.subscription_id()
        ccr_i.bearer_usage = E_BEARER_USAGE_GENERAL
        ccr_i.called_station_id = subscriber.apn.apn
        ccr_i.rat_type = E_RAT_TYPE_EUTRAN
        ccr_i.ip_can_type = E_IP_CAN_TYPE_3GPP_EPS
        ccr_i.network_request_support = E_NETWORK_REQUEST_SUPPORT_NETWORK_REQUEST_SUPPORTED
        ccr_i.event_trigger = []
        ccr_i.event_trigger.append(E_EVENT_TRIGGER_RAT_CHANGE)
        ccr_i.event_trigger.append(E_EVENT_TRIGGER_QOS_CHANGE)
        ccr_i.event_trigger.append(E_EVENT_TRIGGER_USAGE_REPORT)
        ccr_i.event_trigger.append(E_EVENT_TRIGGER_IP_CAN_CHANGE)
        ccr_i.event_trigger.append(E_EVENT_TRIGGER_PLMN_CHANGE)
        self.gx_app.send_request(ccr_i)
