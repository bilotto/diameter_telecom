from ._entity import DiameterEntity
from ..diameter.handle_request import handle_request_gx, handle_request_rx, handle_request_sy
from typing import List, Dict, Callable, Optional
from ..diameter.helpers import Node, create_node
from diameter_telecom.diameter.app import GxApplication, RxApplication, SyApplication

class PCRF(DiameterEntity):
    def __init__(self, origin_host: str, realm_name: str,
                 ip_addresses: List[str],
                 tcp_port: int = None, sctp_port: int = None,
                 vendor_ids: List[int] = None,
                 max_threads: int = 1,
                 request_handler: Callable = handle_request_gx):
        # super().__init__(origin_host=origin_host, realm_name=realm_name, ip_addresses=ip_addresses, tcp_port=tcp_port, sctp_port=sctp_port, vendor_ids=vendor_ids)
        self.origin_host = origin_host
        self.realm_name = realm_name
        self.ip_addresses = ip_addresses
        self.tcp_port = tcp_port
        self.sctp_port = sctp_port
        self.vendor_ids = vendor_ids
        self.node: Node = create_node(origin_host, realm_name, ip_addresses, tcp_port, sctp_port, vendor_ids)
        self.gx_app: GxApplication = GxApplication(max_threads=max_threads, request_handler=request_handler)
        self.rx_app: RxApplication = RxApplication(max_threads=max_threads, request_handler=handle_request_rx)
        self.sy_app: SyApplication = SyApplication(max_threads=max_threads, request_handler=handle_request_sy)

