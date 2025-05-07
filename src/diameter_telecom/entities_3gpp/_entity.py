from typing import *
from diameter.message.constants import *
from ..diameter.helpers import Node, Peer, create_node
from ..diameter.app import *
from ..carrier import Carrier

class DiameterEntity:
    def __init__(self, origin_host: str, realm_name: str,
                 ip_addresses: List[str],
                #  port: int, sctp: bool = False,
                 tcp_port: int, sctp_port: int,
                 vendor_ids: List[int] = None):
        self.origin_host = origin_host
        self.realm_name = realm_name
        self.ip_addresses = ip_addresses
        self.tcp_port = tcp_port
        self.sctp_port = sctp_port
        self.vendor_ids = vendor_ids
        self.node: Node = create_node(origin_host, realm_name, ip_addresses, tcp_port, sctp_port, vendor_ids)
        #
        self.gx_app: GxApplication = None
        self.rx_app: RxApplication = None
        self.sy_app: SyApplication = None
        self.all_peers: Dict[str, List[Peer]] = {}
        self.carrier: Carrier = None

    @property
    def peer_uri(self):
        return f"aaa://{self.origin_host}:{self.tcp_port};transport=tcp"
    
    @property
    def gx_peers(self):
        return self.all_peers[APP_3GPP_GX]
    
    @property
    def rx_peers(self):
        return self.all_peers[APP_3GPP_RX]
    
    @property
    def sy_peers(self):
        return self.all_peers[APP_3GPP_SY]
        
    def start(self):
        if self.gx_app:
            self.node.add_application(self.gx_app, self.gx_peers)
        if self.rx_app:
            self.node.add_application(self.rx_app, self.rx_peers)
        if self.sy_app:
            self.node.add_application(self.sy_app, self.sy_peers)
        self.node.start()

    def wait_for_ready(self):
        for app in self.node.applications:
            app.wait_for_ready()

    def add_peer(self, peer: 'DiameterEntity', initiate_connection: bool = False):
        if peer.gx_app:
            if APP_3GPP_GX not in self.all_peers:
                self.all_peers[APP_3GPP_GX] = []
            self.all_peers[APP_3GPP_GX].append(self.node.add_peer(peer.peer_uri, peer.realm_name, peer.ip_addresses, is_persistent=initiate_connection))
        if peer.rx_app:
            if APP_3GPP_RX not in self.all_peers:
                self.all_peers[APP_3GPP_RX] = []
            self.all_peers[APP_3GPP_RX].append(self.node.add_peer(peer.peer_uri, peer.realm_name, peer.ip_addresses, is_persistent=initiate_connection))
        if peer.sy_app:
            if APP_3GPP_SY not in self.all_peers:
                self.all_peers[APP_3GPP_SY] = []
            self.all_peers[APP_3GPP_SY].append(self.node.add_peer(peer.peer_uri, peer.realm_name, peer.ip_addresses, is_persistent=initiate_connection))

    def set_carrier(self, carrier: Carrier):
        self.carrier = carrier

