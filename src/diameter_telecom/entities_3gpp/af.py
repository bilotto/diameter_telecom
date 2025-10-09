from ..app_new.af import AfRxApplication
from typing import List, Callable, Dict, Optional
from ..diameter_layer.handle_request import handle_request_rx
from ..diameter_layer.helpers import Node, Peer, create_node, node_peer_uri
from ..constants import *
from ._diameter_entity import DiameterEntity
import logging
from ..subscriber import Subscribers
from ..app_new.af import AfRxApplication


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
        Initialize AF with either traditional parameters or node injection.
        
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
        # AF-specific initialization: add its own realm to Rx
        # self.add_rx_realm(self.realm_name)

    def setup_app(self, app_id: int, max_threads):
        # logger.info(f"{type(self).__name__} setting up app {app_id} with max_threads {max_threads} and request_handler {request_handler}")
        app_id = int(app_id)
        if app_id == APP_3GPP_RX:
            app = AfRxApplication(max_threads=max_threads)
            if self.subscribers and hasattr(app, 'subscribers'):
                app.subscribers = self.subscribers
            self.node.add_application(app, self.rx_peers, self.rx_realms)
            self.all_applications[APP_3GPP_RX] = app
            logger.info(f"{type(self).__name__} setup Rx application with {len(self.rx_peers)} peers and {self.rx_realms} realms")
        else:
            raise ValueError(f"Invalid app_id: {app_id}")
        self._setup_app_ran = True
        return app
        
    def setup_rx_app(self, max_threads: int = 10):
        self.setup_app(APP_3GPP_RX, max_threads)

    def setup_apps(self, max_threads: int = 10):
        for app_id, peers in self.all_peers.items():
            self.add_realm(app_id, self.realm_name)
            app = self.setup_app(app_id, max_threads)
            if self.subscribers and hasattr(app, 'subscribers'):
                app.subscribers = self.subscribers
        logger.info(f"{type(self).__name__} setup apps with {len(self.all_peers)} peers and {self.realm_name} realm")