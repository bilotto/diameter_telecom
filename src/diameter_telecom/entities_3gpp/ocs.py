from typing import List, Optional
from ..diameter_layer.helpers import Node, Peer, create_node, node_peer_uri
from ..app.sy import SyApplication
from ..constants import APP_3GPP_SY
from ._diameter_entity import DiameterEntity
import logging
logger = logging.getLogger("diameter_telecom")
from ..app_new.ocs import OcsSyApplication
from ..subscriber import Subscribers


class OCS(DiameterEntity):
    """Online Charging System (OCS) entity.
    
    The OCS is responsible for:
    - Real-time charging and balance management
    - Credit authorization and control via Sy interface
    - Integration with billing systems
    - Spending limit enforcement
    
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
        Initialize OCS with either traditional parameters or node injection.
        
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


    def setup_app(self, app_id: int, max_threads):
        logger.info(f"{type(self).__name__} setting up app {app_id} with max_threads {max_threads}")
        app_id = int(app_id)
        if app_id == APP_3GPP_SY:
            app = OcsSyApplication(max_threads=max_threads)
            self.node.add_application(app, self.sy_peers, self.sy_realms)
            self.all_applications[APP_3GPP_SY] = app
            logger.info(f"{type(self).__name__} setup Sy application with {len(self.sy_peers)} peers and {self.sy_realms} realms")
        else:
            raise ValueError(f"Invalid app_id: {app_id}")
        self._setup_app_ran = True
        return app

    def setup_sy_app(self, max_threads: int = 10):
        self.setup_app(APP_3GPP_SY, max_threads)

    def setup_apps(self, max_threads: int = 10):
        for app_id, peers in self.all_peers.items():
            self.add_realm(app_id, self.realm_name)
            app = self.setup_app(app_id, max_threads)
            if self.subscribers and hasattr(app, 'subscribers'):
                app.subscribers = self.subscribers
        logger.info(f"{type(self).__name__} setup apps with {len(self.all_peers)} peers and {self.realm_name} realm")