from ..diameter.app import *
from typing import List, Callable
from ._entity import DiameterEntity
# from ..diameter.handle_request import handle_request_rx
from diameter.message import Message
from ..diameter.app import CustomSimpleThreadingApplication
import logging
logger = logging.getLogger(__name__)
from ..diameter.constants import *
from diameter.node.peer import PEER_READY_STATES
import time

def handle_request_dsc(app: CustomSimpleThreadingApplication, message: Message):
    origin_host = message.origin_host
    origin_realm = message.origin_realm
    destination_host = message.destination_host
    destination_realm = message.destination_realm
    #
    logger.info(f"Received message {message} from {origin_realm} to {destination_realm}")
    message.route_record.append(origin_host)
    peer_list = []
    for peer in app.node.peers.values():
        logger.debug(f"Checking peer {peer.node_name} with realm {peer.realm_name}")
        if peer.realm_name.encode() == destination_realm:
            if peer.connection and peer.connection.state in PEER_READY_STATES:
                peer_list.append(peer)
    
    if not peer_list:
        logger.error(f"No available peers found for realm {destination_realm}")
        return False
        
    logger.debug(f"Found {len(peer_list)} peers for realm {destination_realm}")
    peer = min(peer_list, key=lambda c: c.counters.requests)
    logger.info(f"Selected peer {peer.node_name} for routing")
    
    try:
        answer = app.node.send_message(peer.connection, message)
        answer = app.send_request(message)
        if answer:
            logger.info(f"Received answer from {peer.node_name}")
            # Route the answer back to the original sender
            app.send_answer(answer)
            return True
        else:
            logger.error(f"No answer received from {peer.node_name}")
            return False
    except Exception as e:
        logger.error(f"Error routing message: {str(e)}")
        return False

# def handle_request_dsc(app: CustomSimpleThreadingApplication, message: Message):
#     origin_host = message.origin_host
#     origin_realm = message.origin_realm
#     destination_host = message.destination_host
#     destination_realm = message.destination_realm
#     #
#     message.route_record.append(origin_host)
#     answer = app.send_request(message)
#     if answer:
#         # answer.route_record.append(app.node.origin_host)
#         app.send_answer(answer)
#     app.stats.increment_based_on_answer(answer)
#     return True


class DSC(DiameterEntity):
    def __init__(self, origin_host: str, realm_name: str,
                 ip_addresses: List[str],
                 tcp_port: int = None, sctp_port: int = None,
                 vendor_ids: List[int] = None,
                 max_threads: int = 1,
                 request_handler: Callable = handle_request_dsc):
        super().__init__(origin_host=origin_host, realm_name=realm_name, ip_addresses=ip_addresses, tcp_port=tcp_port, sctp_port=sctp_port, vendor_ids=vendor_ids)
        self.gx_app: GxApplication = GxApplication(max_threads=max_threads, request_handler=request_handler)
        self.rx_app: RxApplication = RxApplication(max_threads=max_threads, request_handler=request_handler)
        self.sy_app: SyApplication = SyApplication(max_threads=max_threads, request_handler=request_handler)
