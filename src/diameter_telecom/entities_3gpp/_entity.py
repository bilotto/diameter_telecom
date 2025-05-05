from typing import List, Dict, Callable, Optional
from diameter.message.constants import *
from ..diameter.helpers import Node, Peer, create_node, add_peers
from ..diameter.app import *
from ..carrier import Carrier

class DiameterEntity:
    def __init__(self,
                 node: Optional[Node] = None,
                 origin_host: Optional[str] = None,
                 origin_realm: Optional[str] = None,
                 ip_addresses: Optional[List[str]] = None,
                 port: Optional[int] = None,
                 sctp: Optional[bool] = False,
                 vendor_ids: Optional[List[int]] = [VENDOR_ETSI, VENDOR_TGPP, VENDOR_TGPP2],
                 ):
        if node is not None:
            self.node = node
        else:
            if not all([origin_host, origin_realm, ip_addresses, port]):
                raise ValueError("When not providing a node, origin_host, origin_realm, ip_addresses, and port are required")
            self.node = create_node(origin_host, origin_realm, ip_addresses, port, sctp, vendor_ids)
        self.carrier: Carrier = None
        self.gx_app: GxApplication = None
        self.rx_app: RxApplication = None
        self.sy_app: SyApplication = None
        self.gx_peers: List[Peer] = None
        self.rx_peers: List[Peer] = None
        self.sy_peers: List[Peer] = None

    def start(self):
        self.node.start()

    def wait_for_ready(self):
        for app in self.node.applications:
            app.wait_for_ready()

    def add_gx_peers(self, peers_list: List[Dict]):
        self.gx_peers = add_peers(self.node, peers_list)

    def add_rx_peers(self, peers_list: List[Dict]):
        self.rx_peers = add_peers(self.node, peers_list)

    def add_sy_peers(self, peers_list: List[Dict]):
        self.sy_peers = add_peers(self.node, peers_list)

    def add_gx_application(self, request_handler: Callable, realms: List[str] = None):
        self.gx_app = GxApplication(request_handler=request_handler)
        self.node.add_application(self.gx_app, self.gx_peers, realms)

    def add_rx_application(self, request_handler: Callable, realms: List[str] = None):
        self.rx_app = RxApplication(request_handler=request_handler)
        self.node.add_application(self.rx_app, self.rx_peers, realms)

    def add_sy_application(self, request_handler: Callable, realms: List[str] = None):
        self.sy_app = SyApplication(request_handler=request_handler)
        self.node.add_application(self.sy_app, self.sy_peers, realms)

    def set_carrier(self, carrier: Carrier):
        self.carrier = carrier