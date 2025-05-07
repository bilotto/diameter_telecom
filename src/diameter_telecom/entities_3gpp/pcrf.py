from ._entity import DiameterEntity
from ..diameter.handle_request import handle_request_gx, handle_request_rx, handle_request_sy
from typing import List, Dict, Callable, Optional
from ..diameter.helpers import Node
from diameter_telecom.diameter.app import GxApplication

class PCRF(DiameterEntity):
    def __init__(self, origin_host: str, realm_name: str,
                 ip_addresses: List[str],
                 tcp_port: int = None, sctp_port: int = None,
                 vendor_ids: List[int] = None,
                 max_threads: int = 1,
                 request_handler: Callable = handle_request_gx):
        super().__init__(origin_host=origin_host, realm_name=realm_name, ip_addresses=ip_addresses, tcp_port=tcp_port, sctp_port=sctp_port, vendor_ids=vendor_ids)
        self.gx_app: GxApplication = GxApplication(max_threads=max_threads, request_handler=request_handler)

