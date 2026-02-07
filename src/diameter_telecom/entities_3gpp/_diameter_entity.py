import logging
from typing import List, Callable, Optional, Dict

from diameter.message import Message
from diameter.node.peer import PEER_READY_STATES

from ..constants import APP_3GPP_GX, APP_3GPP_RX, APP_3GPP_SY
from ..diameter_layer.helpers import Node, Peer
from ..app.custom_simple_threading_application import CustomSimpleThreadingApplication
from ..app.gx import GxApplication
from ..app.rx import RxApplication
from ..app.sy import SyApplication
from diameter.node.application import Application, ThreadingApplication, SimpleThreadingApplication


from ..subscriber import Subscribers
from ..session_manager.session_manager import SessionManager

# logging.getLogger("diameter_telecom.entities_3gpp").setLevel(logging.DEBUG)
logger = logging.getLogger("diameter_telecom.entities_3gpp")



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
                 vendor_ids: List[int] = [10415],
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
        self.session_manager: SessionManager = None
        self.subscribers: Subscribers = None
        logger.debug(f"Initialized {type(self).__name__} entity {self.origin_host}")

    @property
    def gx_app(self):
        return self.all_applications.get(APP_3GPP_GX, None)

    @property
    def rx_app(self):
        return self.all_applications.get(APP_3GPP_RX, None)

    @property
    def sy_app(self):
        return self.all_applications.get(APP_3GPP_SY, None)

    @property
    def peers(self):
        return self.all_peers
    
    @property
    def realms(self):
        return self.all_realms
    
    @property
    def applications(self):
        return self.all_applications

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

    @property
    def setup_app_ran(self):
        return self._setup_app_ran or len(self.all_applications) > 0

    def set_session_manager(self, session_manager: SessionManager):
        self.session_manager = session_manager

    def set_subscribers(self, subscribers: Subscribers):
        self.subscribers = subscribers 

    def add_node_as_peer(self, node_: Node, app_id: int, initiate_connection: bool = False, is_default: bool = False):
        app_id = int(app_id)
        if app_id not in self.all_peers:
            self.all_peers[app_id] = []
        logger.info(f"{type(self).__name__} adding node {node_.origin_host} as peer for app {app_id}")
        self.all_peers[app_id].append(self.node.add_peer(node_peer_uri(node_), node_.realm_name, node_.ip_addresses, is_persistent=initiate_connection, is_default=is_default))
        self.add_realm(app_id, node_.realm_name)

    def add_realm(self, app_id: int, realm_name: str):
        app_id = int(app_id)
        if app_id not in self.all_realms:
            self.all_realms[app_id] = []
        if realm_name not in self.all_realms[app_id]:
            logger.info(f"{type(self).__name__} adding realm {realm_name} to app {app_id}")
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
            app = GxApplication(max_threads=max_threads, request_handler=request_handler)
            self.node.add_application(app, self.gx_peers, self.gx_realms)
            self.all_applications[APP_3GPP_GX] = app
            logger.info(f"{type(self).__name__} setup Gx application with {len(self.gx_peers)} peers and {self.gx_realms} realms")
        elif app_id == APP_3GPP_RX:
            app = RxApplication(max_threads=max_threads, request_handler=request_handler)
            self.node.add_application(app, self.rx_peers, self.rx_realms)
            self.all_applications[APP_3GPP_RX] = app
            logger.info(f"{type(self).__name__} setup Rx application with {len(self.rx_peers)} peers and {self.rx_realms} realms")
        elif app_id == APP_3GPP_SY:
            app = SyApplication(max_threads=max_threads, request_handler=request_handler)
            self.node.add_application(app, self.sy_peers, self.sy_realms)
            self.all_applications[APP_3GPP_SY] = app
            logger.info(f"{type(self).__name__} setup Sy application with {len(self.sy_peers)} peers and {self.sy_realms} realms")
        else:
            raise ValueError(f"Invalid app_id: {app_id}")
        self._setup_app_ran = True
        return app

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
        if not self.setup_app_ran:
            logger.error("setup_app must be called before start")
            raise ValueError("setup_app must be called before start")
        logger.info(f"Starting {type(self).__name__} entity {self.origin_host}")
        if not self.node.applications:
            raise ValueError("Node applications are not set")
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
        logger.debug(f"Waiting for {type(self).__name__} {self.origin_host} to be ready...")
        for app in self.all_applications.values():
            app.wait_for_ready()
        logger.info(f"{type(self).__name__} entity {self.origin_host} is ready")

    def to_dict(self):
        entity_dict_ = dict()
        entity_type = type(self).__name__
        entity_dict_[entity_type] = dict()
        entity_dict = dict()
        entity_dict['origin_host'] = self.node.origin_host
        entity_dict['realm_name'] = self.node.realm_name
        entity_dict['ip_addresses'] = []
        for ip_address in self.node.ip_addresses:
            entity_dict['ip_addresses'].append(ip_address)
        entity_dict['tcp_port'] = self.node.tcp_port
        entity_dict['vendor_ids'] = []
        for vendor_id in self.node.vendor_ids:
            entity_dict['vendor_ids'].append(vendor_id)
        entity_dict['applications'] = []
        for app_id, app in self.all_applications.items():
            app_dict = dict()
            app_dict['app_id'] = app_id
            app_dict['peers'] = []
            app_dict['additional_realms'] = []
            for realm_name in self.all_realms[app_id]:
                app_dict['additional_realms'].append(realm_name)
            for peer in self.all_peers[app_id]:
                peer_dict = dict()
                peer_dict['peer_host'] = peer.node_name
                peer_dict['peer_realm'] = peer.realm_name
                peer_dict['ip_addresses'] = []
                for ip_address in peer.ip_addresses:
                    peer_dict['ip_addresses'].append(ip_address)
                peer_dict['peer_port'] = peer.port
                peer_dict['initiate_connection'] = peer.persistent
                app_dict['peers'].append(peer_dict)
            entity_dict['applications'].append(app_dict)
        entity_dict_[entity_type] = entity_dict
        return entity_dict_

    def _add_application(self, app: Application):
        app_id = int(app.application_id)
        peers = self.all_peers.get(app_id, [])
        realms = self.all_realms.get(app_id, [])
        if not peers or not realms:
            raise ValueError(f"Peers or realms are not set for app {app_id}")
        self.node.add_application(app, peers, realms)
        self.all_applications[app_id] = app