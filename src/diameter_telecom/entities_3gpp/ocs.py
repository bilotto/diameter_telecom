from ..diameter.handle_request import handle_request
from typing import List, Dict, Callable, Optional
from ..diameter.helpers import Node, Peer, create_node, node_peer_uri
from diameter_telecom.diameter.app import SyApplication
from ..diameter.constants import *
from .dsc import DSC
import logging
logger = logging.getLogger(__name__)


class OCS(DSC):
    """Online Charging System (OCS) entity.
    
    The OCS is responsible for:
    - Real-time charging and balance management
    - Credit authorization and control via Sy interface
    - Integration with billing systems
    - Spending limit enforcement
    
    Inherits from DSC (Diameter Signaling Controller) which provides the complete
    Diameter infrastructure for all applications.
    """
    
    def __init__(self, origin_host: str, realm_name: str,
                 ip_addresses: List[str],
                 tcp_port: int = None, sctp_port: int = None,
                 vendor_ids: List[int] = None):
        super().__init__(origin_host, realm_name, ip_addresses, tcp_port, sctp_port, vendor_ids)
        # OCS-specific initialization: add its own realm to Sy
        self.add_sy_realm(self.realm_name)

    # OCS only needs Sy application - inherits setup_sy_app from DSC
