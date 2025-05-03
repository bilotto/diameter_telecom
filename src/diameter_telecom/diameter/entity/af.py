from diameter_telecom.diameter.helpers import add_peers
from diameter_telecom.diameter.app.rx import RxApplication
from typing import List, Dict, Callable
from ._entity import DiameterEntity
from ..handle_request import handle_request_rx

class AF(DiameterEntity):
    def __init__(self, origin_host, origin_realm, ip_addresses, port, sctp, vendor_ids):
        super().__init__(origin_host, origin_realm, ip_addresses, port, sctp, vendor_ids)
        self.rx_app: RxApplication = None

    def add_rx_peers(self, peers_list: List[Dict], request_handler: Callable = handle_request_rx, realms: List[str] = None):
        self.rx_app = RxApplication(request_handler=request_handler)
        self.node.add_application(self.rx_app, add_peers(self.node, peers_list), realms)

