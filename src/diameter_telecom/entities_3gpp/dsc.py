from ._diameter_entity import DiameterEntity, node_peer_uri, PEER_READY_STATES
from ..diameter.constants import APP_3GPP_GX, APP_3GPP_RX, APP_3GPP_SY
from ..diameter.app import *
from diameter.message import Message
from typing import Callable
import logging

logger = logging.getLogger("diameter_telecom.entities_3gpp")

def handle_request_dsc(app, message: Message):
    """DSC-specific request handler for routing messages."""
    origin_host = message.origin_host
    origin_realm = message.origin_realm
    destination_host = message.destination_host
    destination_realm = message.destination_realm
    
    logger.info(f"Received message {message} from {origin_realm} to {destination_realm}")
    message.route_record.append(origin_host)
    answer = app.send_request(message)
    return answer

class DSC(DiameterEntity):
    """Diameter Signaling Controller (DSC) entity.
    
    The DSC is a generic Diameter entity that can handle all 3GPP applications
    (GX, RX, SY) and provides routing capabilities for Diameter messages.
    """
    
    def setup_apps(self, max_threads: int = 10):
        for app_id, peers in self.all_peers.items():
            self.add_realm(app_id, self.realm_name)
            self.setup_app(app_id, max_threads, handle_request_dsc)

    def wait_for_ready(self):
        import time
        logger.debug(f"Waiting for {type(self).__name__} {self.origin_host} to be ready...")
        for peer in self.node.peers.values():
            if peer.connection:
                if not peer.connection.state in PEER_READY_STATES:
                    logger.debug(f"Peer {peer.node_name} is in state {peer.connection.state}")
                    time.sleep(0.5)
                else:
                    logger.debug(f"Peer {peer.node_name} is in state {peer.connection.state}")
        logger.info(f"{type(self).__name__} entity {self.origin_host} is ready")
