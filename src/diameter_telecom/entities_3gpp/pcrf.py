from typing import List, Dict, Callable, Optional
from ..diameter.helpers import Node, Peer, create_node, node_peer_uri
from ..diameter.handle_request import handle_request
from ..diameter.constants import *
from diameter_telecom.diameter.app import GxApplication, RxApplication, SyApplication
from ._diameter_entity import DiameterEntity
import logging
logger = logging.getLogger("diameter_telecom.entities_3gpp")


class PCRF(DiameterEntity):
    """Policy and Charging Rules Function (PCRF) entity.
    
    The PCRF is the central policy decision point in 3GPP networks that:
    - Provides policy rules to PCEF via Gx interface
    - Receives application requests from AF via Rx interface  
    - Manages spending limits with OCS via Sy interface
    
    Inherits from DSC (Diameter Signaling Controller) which provides the complete
    Diameter infrastructure for all applications.
    """
    
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
        Initialize PCRF with either traditional parameters or node injection.
        
        Args:
            origin_host: Node hostname (required if node not provided)
            realm_name: Node realm (required if node not provided)
            ip_addresses: Node IP addresses (required if node not provided)
            tcp_port: TCP port (optional)
            sctp_port: SCTP port (optional)
            vendor_ids: Vendor IDs (optional)
            node: Pre-created Node object (alternative to above parameters)
        """
        super().__init__(
            origin_host=origin_host,
            realm_name=realm_name,
            ip_addresses=ip_addresses,
            tcp_port=tcp_port,
            sctp_port=sctp_port,
            vendor_ids=vendor_ids,
            node=node
        )
        # PCRF-specific initialization: add its own realm to all applications it supports
        # self.add_gx_realm(self.realm_name)  # For PCEF communication
        # self.add_rx_realm(self.realm_name)  # For AF communication  
        # self.add_sy_realm(self.realm_name)  # For OCS communication

    def setup_apps(self, max_threads: int = 10):
        for app_id, peers in self.all_peers.items():
            self.add_realm(app_id, self.realm_name)
            self.setup_app(app_id, max_threads, handle_request)