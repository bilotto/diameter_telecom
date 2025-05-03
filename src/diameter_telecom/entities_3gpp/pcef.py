from ..diameter.helpers import add_peers
from ..diameter.app.gx import GxApplication
from typing import List, Dict, Callable
from ._entity import DiameterEntity
from ..diameter.handle_request import handle_request_gx

class PCEF(DiameterEntity):
    def __init__(self, origin_host, origin_realm, ip_addresses, port, sctp, vendor_ids):
        super().__init__(origin_host, origin_realm, ip_addresses, port, sctp, vendor_ids)
        self.gx_app: GxApplication = None

    def add_gx_peers(self, peers_list: List[Dict], request_handler: Callable = handle_request_gx, realms: List[str] = None):
        self.gx_app = GxApplication(request_handler=request_handler)
        self.node.add_application(self.gx_app, add_peers(self.node, peers_list), realms)