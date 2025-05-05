from ..diameter.helpers import add_peers
from ..diameter.app.rx import RxApplication
from typing import List, Dict, Callable
from ._entity import DiameterEntity
from ..diameter.handle_request import handle_request_rx

class AF(DiameterEntity):
    def __init__(self, origin_host, origin_realm, ip_addresses, port, sctp, vendor_ids):
        super().__init__(origin_host, origin_realm, ip_addresses, port, sctp, vendor_ids)
        self.rx_app: RxApplication = None

    def setup_rx(self, peers_list: List[Dict], request_handler: Callable = handle_request_rx, realms: List[str] = None):
        self.add_rx_peers(peers_list, request_handler, realms)
        self.add_rx_application(request_handler, realms)

