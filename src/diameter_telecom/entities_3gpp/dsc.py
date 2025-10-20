from diameter.node.application import Application

from ._diameter_entity import DiameterEntity, node_peer_uri, PEER_READY_STATES
from ..constants import APP_3GPP_GX, APP_3GPP_RX, APP_3GPP_SY
from ..app import *
from ..diameter_layer import Message, dump
from typing import Callable
import logging

logger = logging.getLogger("diameter_telecom.entities_3gpp.dsc")

def handle_request_dsc(app: Application, message: Message):
    """DSC-specific request handler for routing messages."""
    message.route_record.append(message.origin_host)
    logger.debug("Routing message to application")
    origin_host = message.origin_host.decode()
    origin_realm = message.origin_realm.decode()
    destination_host = message.destination_host.decode()
    destination_realm = message.destination_realm.decode()
    if peer := app.node.peers.get(destination_host):
        logger.debug(f"Peer {destination_host} found. Routing message to it")
        if destination_realm == peer.realm_name:
            logger.debug(f"Destination realm {destination_realm} matches peer realm {peer.realm_name}. Routing message to it")
        else:
            logger.error(f"Destination realm {destination_realm} does not match peer realm {peer.realm_name}. Routing message to it")
        # logger.error(f"Peer {destination_host} not found. Trying anyway")

    logger.debug(f"DSC Request: \n{dump(message)}")
    # This routes the request to the next application
    answer = app.send_request(message)

    logger.debug("Sending answer to destination")
    logger.debug(f"DSC Answer: \n{dump(answer)}")
    return answer

class DSC(DiameterEntity):
    """Diameter Signaling Controller (DSC) entity.
    
    The DSC is a generic Diameter entity that can handle all 3GPP applications
    (GX, RX, SY) and provides routing capabilities for Diameter messages.
    """
    
    def setup_apps(self, max_threads: int = 10, request_handler: callable = handle_request_dsc):
        for app_id, peers in self.all_peers.items():
            self.add_realm(app_id, self.realm_name)
            self.setup_app(app_id, max_threads, request_handler)

    def wait_for_ready(self, timeout: int = 30):
        import time
        logger.debug(f"Waiting for {type(self).__name__} {self.origin_host} to be ready...")
        for peer in self.node.peers.values():
            if peer.connection:
                if not peer.connection.state in PEER_READY_STATES:
                    logger.debug(f"Peer {peer.node_name} is in state {peer.connection.state}")
                    if timeout > 0:
                        timeout -= 0.5
                    else:
                        raise TimeoutError(f"Peer {peer.node_name} is not ready after {timeout} seconds")
                    time.sleep(0.5)
                else:
                    logger.debug(f"Peer {peer.node_name} is in state {peer.connection.state}")
        logger.info(f"{type(self).__name__} entity {self.origin_host} is ready")
