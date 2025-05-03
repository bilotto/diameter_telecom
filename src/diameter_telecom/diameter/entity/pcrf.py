from ._entity import DiameterEntity
from diameter_telecom.diameter.helpers import create_node, add_peers
from diameter_telecom.diameter.app.gx import GxApplication
from diameter_telecom.diameter.app.rx import RxApplication
from diameter_telecom.diameter.app.sy import SyApplication
from ..handle_request import *
from typing import List, Dict

class PCRF(DiameterEntity):
    def __init__(self, origin_host, origin_realm, ip_addresses, port, sctp, vendor_ids):
        super().__init__(origin_host, origin_realm, ip_addresses, port, sctp, vendor_ids)
        self.gx_app: GxApplication = None
        self.rx_app: RxApplication = None
        self.sy_app: SyApplication = None

    def add_gx_peers(self, peers_list: List[Dict], realms: List[str] = None):
        self.gx_app = GxApplication(request_handler=handle_request_gx)
        self.node.add_application(self.gx_app, add_peers(self.node, peers_list), realms)

    def add_rx_peers(self, peers_list: List[Dict], realms: List[str] = None):
        self.rx_app = RxApplication(request_handler=handle_request_rx)
        self.node.add_application(self.rx_app, add_peers(self.node, peers_list), realms)

    def add_sy_peers(self, peers_list: List[Dict], realms: List[str] = None):
        self.sy_app = SyApplication(request_handler=handle_request_sy)
        self.node.add_application(self.sy_app, add_peers(self.node, peers_list), realms)

