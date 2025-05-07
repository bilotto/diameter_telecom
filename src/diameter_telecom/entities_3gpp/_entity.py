from typing import *
from diameter.message.constants import *
from ..diameter.helpers import Node, Peer, create_node
from ..diameter.app import *
from ..carrier import Carrier
import logging
logger = logging.getLogger(__name__)

def node_peer_uri(node: Node):
    if node.tcp_port:
        return f"aaa://{node.origin_host}:{node.tcp_port};transport=tcp"
    elif node.sctp_port:
        return f"aaa://{node.origin_host}:{node.sctp_port};transport=sctp"
    else:
        raise ValueError(f"Node {node.origin_host} has no TCP or SCTP port")


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
        self.all_realms: Dict[str, List[str]] = {}
        self.carrier: Carrier = None

    @property
    def peer_uri(self):
        return f"aaa://{self.origin_host}:{self.tcp_port};transport=tcp"
    
    @property
    def gx_peers(self):
        return self.all_peers.get(APP_3GPP_GX, [])
    
    @property
    def gx_realms(self):
        return self.all_realms.get(APP_3GPP_GX, [])
    
    @property
    def rx_peers(self):
        return self.all_peers.get(APP_3GPP_RX, [])
    
    @property
    def rx_realms(self):
        return self.all_realms.get(APP_3GPP_RX, [])
    
    @property
    def sy_peers(self):
        return self.all_peers.get(APP_3GPP_SY, [])
    
    @property
    def sy_realms(self):
        return self.all_realms.get(APP_3GPP_SY, [])
        
    def start(self):
        if self.gx_app and self.gx_peers:
            logger.info(f"Starting GxApplication in node {self.node.origin_host} with {len(self.gx_peers)} peers and {len(self.gx_realms)} realms. Realms: {self.gx_realms}")
            self.node.add_application(self.gx_app, self.gx_peers, self.gx_realms)
        if self.rx_app and self.rx_peers:
            logger.info(f"Starting RxApplication in node {self.node.origin_host} with {len(self.rx_peers)} peers and {len(self.rx_realms)} realms. Realms: {self.rx_realms}")
            self.node.add_application(self.rx_app, self.rx_peers, self.rx_realms)
        if self.sy_app and self.sy_peers:
            logger.info(f"Starting SyApplication in node {self.node.origin_host} with {len(self.sy_peers)} peers and {len(self.sy_realms)} realms. Realms: {self.sy_realms}")
            self.node.add_application(self.sy_app, self.sy_peers, self.sy_realms)
        self.node.start()

    def stop(self):
        if self.node._started:
            self.node.stop()

    def wait_for_ready(self):
        for app in self.node.applications:
            app.wait_for_ready()

    def add_peer(self, peer: 'DiameterEntity', initiate_connection: bool = False):
        added_peer = self.node.add_peer(peer.peer_uri, peer.realm_name, peer.ip_addresses, is_persistent=initiate_connection)
        if peer.gx_app:
            if APP_3GPP_GX not in self.all_peers:
                self.all_peers[APP_3GPP_GX] = []
            self.all_peers[APP_3GPP_GX].append(added_peer)
            self.add_gx_realm(peer.realm_name)
            # for realm in peer.all_realms.get(APP_3GPP_GX, []):
            #     self.add_realm(APP_3GPP_GX, realm)
        if peer.rx_app:
            if APP_3GPP_RX not in self.all_peers:
                self.all_peers[APP_3GPP_RX] = []
            self.all_peers[APP_3GPP_RX].append(added_peer)
            self.add_rx_realm(peer.realm_name)
            # for realm in peer.all_realms.get(APP_3GPP_RX, []):
            #     self.add_realm(APP_3GPP_RX, realm)
        if peer.sy_app:
            if APP_3GPP_SY not in self.all_peers:
                self.all_peers[APP_3GPP_SY] = []
            self.all_peers[APP_3GPP_SY].append(added_peer)
            self.add_sy_realm(peer.realm_name)
            # for realm in peer.all_realms.get(APP_3GPP_SY, []):
            #     self.add_realm(APP_3GPP_SY, realm)

    def add_node_as_peer(self, node_: Node, app_id: str, initiate_connection: bool = False):
        if app_id not in self.all_peers:
            self.all_peers[app_id] = []
        self.all_peers[app_id].append(self.node.add_peer(node_peer_uri(node_), node_.realm_name, node_.ip_addresses, is_persistent=initiate_connection))

    def set_carrier(self, carrier: Carrier):
        self.carrier = carrier

    def add_realm(self, app_id: str, realm_name: str):
        if app_id not in self.all_realms:
            self.all_realms[app_id] = []
        if realm_name not in self.all_realms[app_id]:
            self.all_realms[app_id].append(realm_name)

    def add_gx_realm(self, realm_name: str):
        if realm_name not in self.gx_realms:
            self.add_realm(APP_3GPP_GX, realm_name)

    def add_rx_realm(self, realm_name: str):
        if realm_name not in self.rx_realms:
            self.add_realm(APP_3GPP_RX, realm_name)

    def add_sy_realm(self, realm_name: str):
        if realm_name not in self.sy_realms:
            self.add_realm(APP_3GPP_SY, realm_name)


