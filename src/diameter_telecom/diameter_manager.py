from typing import List, Dict
import logging
logger = logging.getLogger("diameter_telecom.diameter_manager")
from dataclasses import dataclass, field

# A class to help create and manage the 3GPP nodes (PCEF, PCRF, AF, OCS, DSC). It links all the entities with same subscribers and session manager.
from .session_manager import SessionManager
from .subscriber import Subscribers
from .entities_3gpp import PCEF, PCRF, AF, OCS, DSC
from .entities_3gpp._diameter_entity import DiameterEntity
from .app_new.common import CommonThreadingApplication

from .service.service import ApplicationService

from .diameter_layer import Node

def define_node_startup_order(nodes_to_start: List[Node]) -> List[str]:
    # nodes_to_start = [entity.node for entity in nodes_to_start]
    # Analyze peer relationships to determine startup order
    accepting_nodes: set = set()  # Nodes that accept connections (start first)
    initiating_nodes = set()  # Nodes that initiate connections (start last)

    for node in nodes_to_start:
        origin_host = node.origin_host
        
        # Check if this node has any persistent peers (initiates connections)
        has_persistent_peers = False
        has_accepting_peers = False
        
        # Analyze the node's peer configurations
        if node.peers:
            for peer_name, peer in node.peers.items():
                # Check if this peer is configured as persistent (initiates connections)
                if peer.persistent:
                    has_persistent_peers = True
                else:
                    has_accepting_peers = True
        
        # Determine startup order based on peer relationships
        if has_persistent_peers and not has_accepting_peers:
            # Node only initiates connections - start last
            initiating_nodes.add(origin_host)
        elif has_accepting_peers and not has_persistent_peers:
            # Node only accepts connections - start first
            accepting_nodes.add(origin_host)
        elif has_persistent_peers and has_accepting_peers:
            # Node both initiates and accepts - start in accepting phase
            accepting_nodes.add(origin_host)
        else:
            # Node without peers or unclear configuration - start in accepting phase
            accepting_nodes.add(origin_host)
    
    # Start nodes in order: accepting first, then initiating
    startup_order = list(accepting_nodes) + list(initiating_nodes)
    return startup_order


@dataclass
class DiameterManager:
    session_manager: SessionManager = field(default_factory=SessionManager)
    subscribers: Subscribers = field(default_factory=Subscribers)
    _nodes: Dict[str, DiameterEntity] = field(default_factory=dict)

    def create_pcef(self, origin_host: str, realm_name: str, ip_addresses: List[str], tcp_port: int, sctp_port: int = None, vendor_ids: List[int] = [10415]) -> PCEF:
        pcef = PCEF(origin_host=origin_host, realm_name=realm_name, ip_addresses=ip_addresses, tcp_port=tcp_port, sctp_port=sctp_port, vendor_ids=vendor_ids)
        self._nodes[pcef.origin_host] = pcef
        return pcef

    def create_pcrf(self, origin_host: str, realm_name: str, ip_addresses: List[str], tcp_port: int, sctp_port: int = None, vendor_ids: List[int] = [10415]) -> PCRF:
        pcrf = PCRF(origin_host=origin_host, realm_name=realm_name, ip_addresses=ip_addresses, tcp_port=tcp_port, sctp_port=sctp_port, vendor_ids=vendor_ids)
        self._nodes[pcrf.origin_host] = pcrf
        return pcrf
    
    def create_af(self, origin_host: str, realm_name: str, ip_addresses: List[str], tcp_port: int, sctp_port: int = None, vendor_ids: List[int] = [10415]) -> AF:
        af = AF(origin_host=origin_host, realm_name=realm_name, ip_addresses=ip_addresses, tcp_port=tcp_port, sctp_port=sctp_port, vendor_ids=vendor_ids)
        self._nodes[af.origin_host] = af
        return af

    def create_ocs(self, origin_host: str, realm_name: str, ip_addresses: List[str], tcp_port: int, sctp_port: int = None, vendor_ids: List[int] = [10415]) -> OCS:
        ocs = OCS(origin_host=origin_host, realm_name=realm_name, ip_addresses=ip_addresses, tcp_port=tcp_port, sctp_port=sctp_port, vendor_ids=vendor_ids)
        self._nodes[ocs.origin_host] = ocs
        return ocs
    
    def create_dsc(self, origin_host: str, realm_name: str, ip_addresses: List[str], tcp_port: int, sctp_port: int = None, vendor_ids: List[int] = [10415]) -> DSC:
        dsc = DSC(origin_host=origin_host, realm_name=realm_name, ip_addresses=ip_addresses, tcp_port=tcp_port, sctp_port=sctp_port, vendor_ids=vendor_ids)
        self._nodes[dsc.origin_host] = dsc
        return dsc

    def create_application_service(self, applications: List[CommonThreadingApplication], diameter_config: dict) -> ApplicationService:
        application_service = ApplicationService(applications=applications, diameter_config=diameter_config, session_manager=self.session_manager, subscribers=self.subscribers)
        return application_service

    def to_dict(self) -> Dict[str, DiameterEntity]:
        return [entity.to_dict() for entity in self._nodes.values()]

    def start(self):
        nodes_to_start: List[Node] = [entity.node for entity in self._nodes.values()]
        startup_order = define_node_startup_order(nodes_to_start)
        for node in startup_order:
            self._nodes[node].start()

    def wait_for_ready(self):
        for i in self._nodes.values():
            i.wait_for_ready()

