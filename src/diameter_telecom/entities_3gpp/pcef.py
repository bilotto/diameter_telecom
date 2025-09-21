from typing import List, Dict, Callable, Optional
from ..diameter.helpers import Node, Peer, create_node, node_peer_uri
from ..diameter.handle_request import handle_request
from ..diameter.constants import *
from diameter_telecom.diameter.app import GxApplication
from .dsc import DSC
import logging
logger = logging.getLogger(__name__)


class PCEF(DSC):
    """Policy and Charging Enforcement Function (PCEF) entity.
    
    The PCEF is responsible for policy enforcement and charging data collection
    in 3GPP networks. It communicates with the PCRF via the Gx interface.
    
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
        Initialize PCEF with either traditional parameters or node injection.
        
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
        # PCEF-specific initialization: add its own realm to Gx  
        self.add_gx_realm(self.realm_name)

    # PCEF only needs Gx application - inherits setup_gx_app from DSC

