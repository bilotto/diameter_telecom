from ..diameter.handle_request import handle_request_sy
from typing import List, Dict, Callable, Optional
from ..diameter.helpers import Node, Peer, create_node
from diameter_telecom.diameter.app import SyApplication
from ..diameter.constants import *
import logging
logger = logging.getLogger(__name__)

def node_peer_uri(node: Node):
    if node.tcp_port:
        return f"aaa://{node.origin_host}:{node.tcp_port};transport=tcp"
    elif node.sctp_port:
        return f"aaa://{node.origin_host}:{node.sctp_port};transport=sctp"
    else:
        raise ValueError(f"Node {node.origin_host} has no TCP or SCTP port")

class OCS():
    def __init__(self, origin_host: str, realm_name: str,
                 ip_addresses: List[str],
                 tcp_port: int = None, sctp_port: int = None,
                 vendor_ids: List[int] = None,
                #  max_threads: int = 10,
                #  request_handler_sy: Callable = handle_request_sy,
                 ):
        self.origin_host = origin_host
        self.realm_name = realm_name
        self.ip_addresses = ip_addresses
        self.tcp_port = tcp_port
        self.sctp_port = sctp_port
        self.vendor_ids = vendor_ids
        self.node: Node = create_node(origin_host, realm_name, ip_addresses, tcp_port, sctp_port, vendor_ids)
        # self.sy_app: SyApplication = SyApplication(max_threads=max_threads, request_handler=request_handler_sy)
        self.all_peers: Dict[str, List[Peer]] = {}
        self.all_realms: Dict[str, List[str]] = {}
        self._setup_app_ran = False
        self.add_sy_realm(self.realm_name)

    @property
    def sy_peers(self):
        return self.all_peers.get(APP_3GPP_SY, [])
    
    @property
    def sy_realms(self):
        return self.all_realms.get(APP_3GPP_SY, [])
    
    def add_node_as_peer(self, node_: Node, app_id: str, initiate_connection: bool = False):
        if app_id not in self.all_peers:
            self.all_peers[app_id] = []
        self.all_peers[app_id].append(self.node.add_peer(node_peer_uri(node_), node_.realm_name, node_.ip_addresses, is_persistent=initiate_connection))

    def add_realm(self, app_id: str, realm_name: str):
        if app_id not in self.all_realms:
            self.all_realms[app_id] = []
        if realm_name not in self.all_realms[app_id]:
            self.all_realms[app_id].append(realm_name)

    def add_sy_realm(self, realm_name: str):
        if realm_name not in self.sy_realms:
            self.add_realm(APP_3GPP_SY, realm_name)

    def setup_app(self, app_id: int, max_threads: int = 1, request_handler: Callable = handle_request_sy):
        if app_id == APP_3GPP_SY:
            self.sy_app = SyApplication(max_threads=max_threads, request_handler=request_handler)
            self.node.add_application(self.sy_app, self.sy_peers, self.sy_realms)
        self._setup_app_ran = True

    def setup_sy_app(self, max_threads: int = 1, request_handler: Callable = handle_request_sy):
        self.setup_app(APP_3GPP_SY, max_threads, request_handler)

    def start(self):
        if not self._setup_app_ran:
            logger.error("setup_app must be called before start")
            return
        # if self.sy_app and self.sy_peers:
        #     logger.info(f"Starting SyApplication in node {self.node.origin_host} with {len(self.sy_peers)} peers and {len(self.sy_realms)} realms. Realms: {self.sy_realms}")
        #     self.node.add_application(self.sy_app, self.sy_peers, self.sy_realms)
        self.node.start()

    def stop(self):
        if self.node._started:
            self.node.stop()

    def wait_for_ready(self):
        for app in self.node.applications:
            app.wait_for_ready()
