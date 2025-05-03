from diameter_telecom.diameter.helpers import create_node, add_peers
from diameter_telecom.diameter.app.gx import GxApplication
from typing import List, Dict

class PCEF:
    def __init__(self, origin_host, origin_realm, ip_addresses, port, sctp, vendor_ids):
        self.node = create_node(origin_host, origin_realm, ip_addresses, port, sctp, vendor_ids)
        self.gx_app: GxApplication = None

    def add_gx_peers(self, peers_list: List[Dict], realms: List[str] = None):
        self.gx_app = GxApplication()
        self.node.add_application(self.gx_app, add_peers(self.node, peers_list), realms)

    def start(self):
        self.node.start()


