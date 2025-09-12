from typing import List, Dict, Callable, Optional
from ..diameter.helpers import Node, Peer, create_node, node_peer_uri
from ..diameter.handle_request import handle_request
from ..diameter.constants import *
from diameter_telecom.diameter.app import GxApplication, RxApplication, SyApplication
from .dsc import DSC
import logging
logger = logging.getLogger(__name__)


class PCRF(DSC):
    """Policy and Charging Rules Function (PCRF) entity.
    
    The PCRF is the central policy decision point in 3GPP networks that:
    - Provides policy rules to PCEF via Gx interface
    - Receives application requests from AF via Rx interface  
    - Manages spending limits with OCS via Sy interface
    
    Inherits from DSC (Diameter Signaling Controller) which provides the complete
    Diameter infrastructure for all applications.
    """
    
    def __init__(self, origin_host: str, realm_name: str,
                 ip_addresses: List[str],
                 tcp_port: int = None, sctp_port: int = None,
                 vendor_ids: List[int] = None):
        super().__init__(origin_host, realm_name, ip_addresses, tcp_port, sctp_port, vendor_ids)
        # PCRF-specific initialization: add its own realm to all applications it supports
        self.add_gx_realm(self.realm_name)  # For PCEF communication
        self.add_rx_realm(self.realm_name)  # For AF communication  
        self.add_sy_realm(self.realm_name)  # For OCS communication

    # PCRF can use all three applications - inherits setup methods from DSC
    # - setup_gx_app() for PCEF communication
    # - setup_rx_app() for AF communication
    # - setup_sy_app() for OCS communication

