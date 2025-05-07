from ..diameter.app.rx import RxApplication
from typing import List, Callable
from ._entity import DiameterEntity
from ..diameter.handle_request import handle_request_rx

class AF(DiameterEntity):
    def __init__(self, origin_host: str, realm_name: str,
                 ip_addresses: List[str],
                 tcp_port: int = None, sctp_port: int = None,
                 vendor_ids: List[int] = None,
                 max_threads: int = 1,
                 request_handler: Callable = handle_request_rx):
        super().__init__(origin_host=origin_host, realm_name=realm_name, ip_addresses=ip_addresses, tcp_port=tcp_port, sctp_port=sctp_port, vendor_ids=vendor_ids)
        self.rx_app: RxApplication = RxApplication(max_threads=max_threads, request_handler=request_handler)
