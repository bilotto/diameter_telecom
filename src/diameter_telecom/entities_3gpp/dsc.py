from ..diameter.app import *
from typing import List, Callable
from ._entity import DiameterEntity
from ..diameter.helpers import Node, Peer, create_node
from diameter.message import Message
from ..diameter.app import *
import logging
logger = logging.getLogger(__name__)
from ..diameter.constants import *
from diameter.node.peer import PEER_READY_STATES
from typing import Dict, List

def handle_request_dsc(app: CustomSimpleThreadingApplication, message: Message):
    origin_host = message.origin_host
    origin_realm = message.origin_realm
    destination_host = message.destination_host
    destination_realm = message.destination_realm
    #
    logger.info(f"Received message {message} from {origin_realm} to {destination_realm}")
    message.route_record.append(origin_host)
    answer = app.send_request(message)
    return answer
    # peer_list = []
    # for peer in app.node.peers.values():
    #     logger.debug(f"Checking peer {peer.node_name} with realm {peer.realm_name}")
    #     if peer.realm_name.encode() == destination_realm:
    #         if peer.connection and peer.connection.state in PEER_READY_STATES:
    #             peer_list.append(peer)
    
    # if not peer_list:
    #     logger.error(f"No available peers found for realm {destination_realm}")
    #     return False
        
    # logger.debug(f"Found {len(peer_list)} peers for realm {destination_realm}")
    # peer = min(peer_list, key=lambda c: c.counters.requests)
    # logger.info(f"Selected peer {peer.node_name} for routing")
    
    try:
        # answer = app.node.send_message(peer.connection, message)
        answer = app.send_request(message)
        if answer:
            # logger.info(f"Received answer from {peer.node_name}")
            # Route the answer back to the original sender
            app.send_answer(answer)
            return True
        else:
            # logger.error(f"No answer received from {peer.node_name}")
            return False
    except Exception as e:
        logger.error(f"Error routing message: {str(e)}")
        return False

def node_peer_uri(node: Node):
    if node.tcp_port:
        return f"aaa://{node.origin_host}:{node.tcp_port};transport=tcp"
    elif node.sctp_port:
        return f"aaa://{node.origin_host}:{node.sctp_port};transport=sctp"
    else:
        raise ValueError(f"Node {node.origin_host} has no TCP or SCTP port")



# class DSC(DiameterEntity):
class DSC():
    def __init__(self, origin_host: str, realm_name: str,
                 ip_addresses: List[str],
                 tcp_port: int = None, sctp_port: int = None,
                 vendor_ids: List[int] = None,):
        # super().__init__(origin_host=origin_host, realm_name=realm_name, ip_addresses=ip_addresses, tcp_port=tcp_port, sctp_port=sctp_port, vendor_ids=vendor_ids)
        self.origin_host = origin_host
        self.realm_name = realm_name
        self.ip_addresses = ip_addresses
        self.tcp_port = tcp_port
        self.sctp_port = sctp_port
        self.vendor_ids = vendor_ids
        self.node: Node = create_node(origin_host, realm_name, ip_addresses, tcp_port, sctp_port, vendor_ids)
        # self.gx_app: GxApplication = GxApplication(max_threads=max_threads, request_handler=request_handler)
        # self.rx_app: RxApplication = RxApplication(max_threads=max_threads, request_handler=request_handler)
        # self.sy_app: SyApplication = SyApplication(max_threads=max_threads, request_handler=request_handler)
        self.all_peers: Dict[str, List[Peer]] = {}
        self.all_realms: Dict[str, List[str]] = {}
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
    
    def add_node_as_peer(self, node_: Node, app_id: str, initiate_connection: bool = False):
        if app_id not in self.all_peers:
            self.all_peers[app_id] = []
        self.all_peers[app_id].append(self.node.add_peer(node_peer_uri(node_), node_.realm_name, node_.ip_addresses, is_persistent=initiate_connection))
        self.add_realm(app_id, node_.realm_name)

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

    def setup_app(self, app_id: int, max_threads, request_handler: Callable):
        if app_id == APP_3GPP_GX:
            self.gx_app = GxApplication(max_threads=max_threads, request_handler=request_handler)
            self.node.add_application(self.gx_app, self.gx_peers, self.gx_realms)
        elif app_id == APP_3GPP_RX:
            self.rx_app = RxApplication(max_threads=max_threads, request_handler=request_handler)
            self.node.add_application(self.rx_app, self.rx_peers, self.rx_realms)
        elif app_id == APP_3GPP_SY:
            self.sy_app = SyApplication(max_threads=max_threads, request_handler=request_handler)
            self.node.add_application(self.sy_app, self.sy_peers, self.sy_realms)
        else:
            raise ValueError(f"Invalid app_id: {app_id}")
        self._setup_app_ran = True

    def setup_gx_app(self, max_threads: int = 10, request_handler: Callable = handle_request_dsc):
        self.setup_app(APP_3GPP_GX, max_threads, request_handler)

    def setup_rx_app(self, max_threads: int = 10, request_handler: Callable = handle_request_dsc):
        self.setup_app(APP_3GPP_RX, max_threads, request_handler)

    def setup_sy_app(self, max_threads: int = 10, request_handler: Callable = handle_request_dsc):
        self.setup_app(APP_3GPP_SY, max_threads, request_handler)

    def start(self):
        if not self._setup_app_ran:
            logger.error("setup_app must be called before start")
            return
        self.node.start()

    def stop(self):
        if self.node._started:
            self.node.stop()

    def wait_for_ready(self):
        for app in self.node.applications:
            app.wait_for_ready()

