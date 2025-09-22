from ..diameter.app.rx import RxApplication
from typing import List, Callable, Dict
from ..diameter.handle_request import handle_request_rx
from ..diameter.constants import *
from ..diameter.helpers import Node, Peer, create_node, node_peer_uri
from ._diameter_entity import DiameterEntity
import logging

logger = logging.getLogger("diameter_telecom.entities_3gpp")


class AF(DiameterEntity):
    """Application Function (AF) entity.
    
    The AF is responsible for:
    - Providing application-specific information to the PCRF
    - Requesting QoS resources via Rx interface
    - Managing media session requirements
    
    Inherits from DSC (Diameter Signaling Controller) which provides the complete
    Diameter infrastructure for all applications.
    """
    
    def __init__(self, origin_host: str, realm_name: str,
                 ip_addresses: List[str],
                 tcp_port: int = None, sctp_port: int = None,
                 vendor_ids: List[int] = None):
        super().__init__(origin_host, realm_name, ip_addresses, tcp_port, sctp_port, vendor_ids)
        # AF-specific initialization: add its own realm to Rx
        self.add_rx_realm(self.realm_name)

    def setup_apps(self, max_threads: int = 10):
        """Setup applications supported by AF (RX only)."""
        self.setup_app(APP_3GPP_RX, max_threads, handle_request_rx)
