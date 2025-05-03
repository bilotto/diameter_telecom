from ._entity import DiameterEntity
from diameter_telecom.diameter.helpers import add_peers
from diameter_telecom.diameter.app.gx import GxApplication
from diameter_telecom.diameter.app.rx import RxApplication
from diameter_telecom.diameter.app.sy import SyApplication
from ..handle_request import *
from typing import List, Dict, Callable

class PCRF(DiameterEntity):
    def __init__(self, origin_host, origin_realm, ip_addresses, port, sctp, vendor_ids):
        super().__init__(origin_host, origin_realm, ip_addresses, port, sctp, vendor_ids)
        self.gx_app: GxApplication = None
        self.rx_app: RxApplication = None
        self.sy_app: SyApplication = None

    def add_gx_peers(self, peers_list: List[Dict], request_handler: Callable = handle_request_gx, realms: List[str] = None):
        self.gx_app = GxApplication(request_handler=request_handler)
        self.node.add_application(self.gx_app, add_peers(self.node, peers_list), realms)

    def add_rx_peers(self, peers_list: List[Dict], request_handler: Callable = handle_request_rx, realms: List[str] = None):
        self.rx_app = RxApplication(request_handler=request_handler)
        self.node.add_application(self.rx_app, add_peers(self.node, peers_list), realms)

    def add_sy_peers(self, peers_list: List[Dict], request_handler: Callable = handle_request_sy, realms: List[str] = None):
        self.sy_app = SyApplication(request_handler=request_handler)
        self.node.add_application(self.sy_app, add_peers(self.node, peers_list), realms)

