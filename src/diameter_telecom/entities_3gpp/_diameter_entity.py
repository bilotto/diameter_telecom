from ..diameter.app import *
from typing import List, Callable, Optional
from ..diameter.helpers import Node, Peer
from diameter.message import Message
from ..diameter.app import *
import logging
logger = logging.getLogger(__name__)
from ..diameter.constants import *
from diameter.node.peer import PEER_READY_STATES
from typing import Dict, List

logging.getLogger("diameter_telecom.entities_3gpp").setLevel(logging.DEBUG)

def node_peer_uri(node: Node):
    if node.tcp_port:
        return f"aaa://{node.origin_host}:{node.tcp_port};transport=tcp"
    elif node.sctp_port:
        return f"aaa://{node.origin_host}:{node.sctp_port};transport=sctp"
    else:
        raise ValueError(f"Node {node.origin_host} has no TCP or SCTP port")

class DiameterEntity:
    def __init__(self, 
                 # Traditional parameters (for backwards compatibility)
                 origin_host: str = None, 
                 realm_name: str = None,
                 ip_addresses: List[str] = None,
                 tcp_port: int = None, 
                 sctp_port: int = None,
                 vendor_ids: List[int] = None,
                 # New node injection parameter
                 node: Optional[Node] = None):
        """
        Initialize with either traditional parameters or node injection.
        
        Args:
            origin_host: Node hostname (required if node not provided)
            realm_name: Node realm (required if node not provided)
            ip_addresses: Node IP addresses (required if node not provided)
            tcp_port: TCP port (optional)
            sctp_port: SCTP port (optional)
            vendor_ids: Vendor IDs (optional)
            node: Pre-created Node object (alternative to above parameters)
            
        Raises:
            ValueError: If neither node nor required parameters are provided
        """
        
        # Validate input parameters
        if node is not None:
            # Node injection pattern
            if not isinstance(node, Node):
                raise TypeError("node must be a Node instance")
            self.node = node
            self.origin_host = node.origin_host
            self.realm_name = node.realm_name
            self.ip_addresses = node.ip_addresses
            self.tcp_port = node.tcp_port
            self.sctp_port = node.sctp_port
            self.vendor_ids = node.vendor_ids
            
        elif origin_host and realm_name and ip_addresses:
            # Traditional pattern (backwards compatible)
            self.origin_host = origin_host
            self.realm_name = realm_name
            self.ip_addresses = ip_addresses
            self.tcp_port = tcp_port
            self.sctp_port = sctp_port
            self.vendor_ids = vendor_ids or [10415]
            # self.node = create_node(origin_host, realm_name, ip_addresses, tcp_port, sctp_port, vendor_ids)
            self.node = Node(origin_host, realm_name, ip_addresses, tcp_port, sctp_port, vendor_ids)
            
        else:
            raise ValueError(
                "Either 'node' parameter or ('origin_host', 'realm_name', 'ip_addresses') "
                "parameters must be provided"
            )
        
        # Initialize common attributes
        self.all_peers: Dict[int, List[Peer]] = {}
        self.all_realms: Dict[int, List[str]] = {}
        self.all_applications: Dict[int, CustomSimpleThreadingApplication] = {}
        self._setup_app_ran = False

    @property
    def peer_uri(self):
        return node_peer_uri(self.node)
    
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
    
    def add_node_as_peer(self, node_: Node, app_id: int, initiate_connection: bool = False):
        app_id = int(app_id)
        if app_id not in self.all_peers:
            self.all_peers[app_id] = []
        self.all_peers[app_id].append(self.node.add_peer(node_peer_uri(node_), node_.realm_name, node_.ip_addresses, is_persistent=initiate_connection))
        self.add_realm(app_id, node_.realm_name)

    def add_realm(self, app_id: int, realm_name: str):
        app_id = int(app_id)
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

    def setup_app(self, app_id: int, max_threads, request_handler: Callable):
        app_id = int(app_id)
        if app_id == APP_3GPP_GX:
            self.gx_app = GxApplication(max_threads=max_threads, request_handler=request_handler)
            self.node.add_application(self.gx_app, self.gx_peers, self.gx_realms)
            self.all_applications[APP_3GPP_GX] = self.gx_app
        elif app_id == APP_3GPP_RX:
            self.rx_app = RxApplication(max_threads=max_threads, request_handler=request_handler)
            self.node.add_application(self.rx_app, self.rx_peers, self.rx_realms)
            self.all_applications[APP_3GPP_RX] = self.rx_app
        elif app_id == APP_3GPP_SY:
            self.sy_app = SyApplication(max_threads=max_threads, request_handler=request_handler)
            self.node.add_application(self.sy_app, self.sy_peers, self.sy_realms)
            self.all_applications[APP_3GPP_SY] = self.sy_app
        else:
            raise ValueError(f"Invalid app_id: {app_id}")
        self._setup_app_ran = True

    def setup_gx_app(self, max_threads: int = 10, request_handler: Callable = None):
        if request_handler is None:
            raise NotImplementedError("Subclasses must provide a request_handler for setup_gx_app")
        self.setup_app(APP_3GPP_GX, max_threads, request_handler)

    def setup_rx_app(self, max_threads: int = 10, request_handler: Callable = None):
        if request_handler is None:
            raise NotImplementedError("Subclasses must provide a request_handler for setup_rx_app")
        self.setup_app(APP_3GPP_RX, max_threads, request_handler)

    def setup_sy_app(self, max_threads: int = 10, request_handler: Callable = None):
        if request_handler is None:
            raise NotImplementedError("Subclasses must provide a request_handler for setup_sy_app")
        self.setup_app(APP_3GPP_SY, max_threads, request_handler)

    def start(self):
        if not self._setup_app_ran:
            logger.error("setup_app must be called before start")
            return
        logger.info(f"Starting {type(self).__name__} entity {self.origin_host}")
        self.node.start()
        logger.debug(f"{type(self).__name__} node started on {self.ip_addresses}:{self.tcp_port}")

    def stop(self):
        logger.info(f"Stopping {type(self).__name__} entity {self.origin_host}")
        if self.node._started:
            self.node.stop()
            logger.debug(f"{type(self).__name__} node stopped")
        else:
            logger.debug(f"{type(self).__name__} node was already stopped")

    def wait_for_ready(self):
        import time
        logger.debug(f"Waiting for {type(self).__name__} {self.origin_host} to be ready...")
        for peer in self.node.peers.values():
            if peer.connection:
                if not peer.connection.state in PEER_READY_STATES:
                    logger.debug(f"Peer {peer.node_name} is in state {peer.connection.state}")
                    time.sleep(0.5)
                else:
                    logger.debug(f"Peer {peer.node_name} is in state {peer.connection.state}")
        logger.info(f"{type(self).__name__} entity {self.origin_host} is ready")

    def to_dict(self):
        entity_dict = dict()
        entity_dict['node'] = dict()
        entity_dict['node']['origin_host'] = self.node.origin_host
        entity_dict['node']['realm_name'] = self.node.realm_name
        entity_dict['node']['ip_addresses'] = self.node.ip_addresses
        entity_dict['node']['tcp_port'] = self.node.tcp_port
        entity_dict['peer_uri'] = self.peer_uri
        entity_dict['all_peers'] = self.all_peers
        entity_dict['all_realms'] = self.all_realms
        entity_dict['all_applications'] = self.all_applications
        entity_dict['_setup_app_ran'] = self._setup_app_ran
        return entity_dict