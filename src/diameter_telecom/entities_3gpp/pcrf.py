from ._entity import DiameterEntity
from ..diameter.handle_request import handle_request_gx, handle_request_rx, handle_request_sy
from typing import List, Dict, Callable, Optional
from ..diameter.helpers import Node

class PCRF(DiameterEntity):
    def __init__(self, 
                 node: Optional[Node] = None,
                 origin_host: Optional[str] = None,
                 origin_realm: Optional[str] = None,
                 ip_addresses: Optional[List[str]] = None,
                 port: Optional[int] = None,
                 sctp: Optional[bool] = False, 
                 vendor_ids: Optional[List[int]] = None):
        super().__init__(node=node,
                        origin_host=origin_host,
                        origin_realm=origin_realm,
                        ip_addresses=ip_addresses,
                        port=port,
                        sctp=sctp,
                        vendor_ids=vendor_ids)

    def setup_gx(self, peers_list: List[Dict], request_handler: Callable = handle_request_gx, realms: List[str] = None):
        """Setup Gx application with peers and request handler"""
        self.add_gx_peers(peers_list)
        self.add_gx_application(request_handler, realms)

    def setup_rx(self, peers_list: List[Dict], request_handler: Callable = handle_request_rx, realms: List[str] = None):
        """Setup Rx application with peers and request handler"""
        self.add_rx_peers(peers_list)
        self.add_rx_application(request_handler, realms)

    def setup_sy(self, peers_list: List[Dict], request_handler: Callable = handle_request_sy, realms: List[str] = None):
        """Setup Sy application with peers and request handler"""
        self.add_sy_peers(peers_list)
        self.add_sy_application(request_handler, realms)