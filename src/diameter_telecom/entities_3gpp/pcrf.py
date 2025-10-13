from typing import List, Dict, Callable, Optional
from ..diameter_layer.helpers import Node, Peer, create_node, node_peer_uri
from ..diameter_layer.handle_request import handle_request
from ..constants import *
from ..app.gx import GxApplication
from ..app.rx import RxApplication
from ..app.sy import SyApplication
from ._diameter_entity import DiameterEntity
import logging
logger = logging.getLogger("diameter_telecom.entities_3gpp")
from ..app_new.pcrf import PcrfGxApplication, PcrfRxApplication, PcrfSyApplication
from ..subscriber import Subscribers


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
                 vendor_ids: List[int] = [10415],
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

    def setup_app(self, app_id: int, max_threads):
        # logger.info(f"{type(self).__name__} setting up app {app_id} with max_threads {max_threads} and request_handler {request_handler}")
        app_id = int(app_id)
        if app_id == APP_3GPP_GX:
            app = PcrfGxApplication(max_threads=max_threads)
            self.node.add_application(app, self.gx_peers, self.gx_realms)
            self.all_applications[APP_3GPP_GX] = app
            logger.info(f"{type(self).__name__} setup Gx application with {len(self.gx_peers)} peers and {self.gx_realms} realms")
        elif app_id == APP_3GPP_RX:
            app = PcrfRxApplication(max_threads=max_threads)
            self.node.add_application(app, self.rx_peers, self.rx_realms)
            self.all_applications[APP_3GPP_RX] = app
            # logger.info(f"{type(self).__name__} setup Rx application with peers {self.rx_peers} and realms {self.rx_realms}")
            logger.info(f"{type(self).__name__} setup Rx application with {len(self.rx_peers)} peers and {self.rx_realms} realms")
        elif app_id == APP_3GPP_SY:
            # self.sy_app = PcrfSyApplication(max_threads=max_threads)
            app = PcrfSyApplication(max_threads=max_threads)
            self.node.add_application(app, self.sy_peers, self.sy_realms)
            self.all_applications[APP_3GPP_SY] = app
            logger.info(f"{type(self).__name__} setup Sy application with {len(self.sy_peers)} peers and {self.sy_realms} realms")
        else:
            raise ValueError(f"Invalid app_id: {app_id}")
        self._setup_app_ran = True
        return app
        
    def setup_gx_app(self, max_threads: int = 10):
        self.setup_app(APP_3GPP_GX, max_threads)

    def setup_rx_app(self, max_threads: int = 10):
        self.setup_app(APP_3GPP_RX, max_threads)

    def setup_sy_app(self, max_threads: int = 10):
        self.setup_app(APP_3GPP_SY, max_threads)

    def setup_apps(self, max_threads: int = 10):
        for app_id, peers in self.all_peers.items():
            self.add_realm(app_id, self.realm_name)
            app = self.setup_app(app_id, max_threads)
            if self.subscribers and hasattr(app, 'subscribers'):
                app.subscribers = self.subscribers
        logger.info(f"{type(self).__name__} setup apps with {len(self.all_peers)} peers and {self.realm_name} realm")