import logging
from typing import List, Dict, Callable, Optional

from ..app.gx import GxApplication

from ..constants import APP_3GPP_GX
from ..diameter_layer.helpers import Node, Peer, create_node, node_peer_uri
from ..diameter_layer.handle_request import handle_request
from ..app_new.pcef import PcefGxApplication
from ._diameter_entity import DiameterEntity
from .ip_queue import IpQueue
from ..subscriber import Subscribers
from ..session_manager.session_manager import SessionManager

logger = logging.getLogger("diameter_telecom.entities_3gpp")

class PCEF(DiameterEntity):
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
                 vendor_ids: List[int] = [10415],
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

        self.ip_queue = IpQueue("10.10.0.0/16")
        self.subscribers: Subscribers = None
        self.session_manager: SessionManager = None
        # PCEF-specific initialization: add its own realm to Gx  
        # self.add_gx_realm(self.realm_name)


    def setup_app(self, app_id: int, max_threads):
        # logger.info(f"{type(self).__name__} setting up app {app_id} with max_threads {max_threads} and request_handler {request_handler}")
        app_id = int(app_id)
        if app_id == APP_3GPP_GX:
            app = PcefGxApplication(max_threads=max_threads)
            if self.subscribers and hasattr(app, 'subscribers'):
                app.subscribers = self.subscribers
            self.node.add_application(app, self.gx_peers, self.gx_realms)
            self.all_applications[APP_3GPP_GX] = app
            logger.info(f"{type(self).__name__} setup Gx application with {len(self.gx_peers)} peers and {self.gx_realms} realms")
        else:
            raise ValueError(f"Invalid app_id: {app_id} for PCEF")
        self._setup_app_ran = True
        return app

    def setup_gx_app(self, max_threads: int = 10):
        self.add_realm(APP_3GPP_GX, self.realm_name)
        self.setup_app(APP_3GPP_GX, max_threads)

    def setup_apps(self, max_threads: int = 10):
        for app_id, peers in self.all_peers.items():
            self.add_realm(app_id, self.realm_name)
            app = self.setup_app(app_id, max_threads)
            if self.subscribers and hasattr(app, 'subscribers'):
                app.subscribers = self.subscribers
        logger.info(f"{type(self).__name__} setup apps with {len(self.all_peers)} peers and {self.realm_name} realm")