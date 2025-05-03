"""
Diameter Node and Peer Management Helpers

This module provides utility functions for managing Diameter nodes and peers.
These functions help in setting up and configuring Diameter protocol connections
between network elements in a telecommunications network.

The functions support both TCP and SCTP transport protocols and provide
flexible configuration options for node and peer management.
"""

from typing import List, Dict
from diameter.node import Node
from diameter.node.node import Peer

def create_node(origin_host: str,
                realm_name: str,
                ip_addresses: List[str],
                port: int,
                sctp: bool = False,
                vendor_ids=[]) -> Node:
    """
    Create a new Diameter node with specified configuration.
    
    This function creates a Diameter node that can act as either a client or server
    in the Diameter protocol. It supports both TCP and SCTP transport protocols.
    
    Args:
        origin_host (str): The hostname of this node
        realm_name (str): The realm name this node belongs to
        ip_addresses (List[str]): List of IP addresses this node listens on
        port (int): Port number for the connection
        sctp (bool, optional): Whether to use SCTP instead of TCP. Defaults to False
        vendor_ids (list, optional): List of vendor IDs supported by this node
        
    Returns:
        Node: A configured Diameter node instance
        
    Example:
        >>> node = create_node("pcrf.example.com", "example.com", ["192.168.1.1"], 3868)
        >>> node = create_node("pcrf.example.com", "example.com", ["192.168.1.1"], 3868, sctp=True)
    """
    if not sctp:
        node = Node(origin_host, realm_name, ip_addresses=ip_addresses, tcp_port=port, vendor_ids=vendor_ids)
    else:
        node = Node(origin_host, realm_name, ip_addresses=ip_addresses, sctp_port=port, vendor_ids=vendor_ids)
    return node

def add_peers(node: Node, peers_list: List[Dict]) -> List[Peer]:
    """
    Add multiple peers to a Diameter node.
    
    This function adds a list of peers to a Diameter node, configuring each peer
    with the specified parameters. It automatically handles the transport protocol
    (TCP or SCTP) based on the node's configuration.
    
    Args:
        node (Node): The Diameter node to add peers to
        peers_list (List[Dict]): List of peer configurations, where each dict contains:
            - host (str): Peer hostname
            - port (int): Peer port number
            - realm (str): Peer realm name
            - ip_addresses (List[str], optional): List of peer IP addresses
            - is_persistent (bool, optional): Whether to maintain persistent connection
            - is_default (bool, optional): Whether this is a default peer
            
    Returns:
        List[Peer]: List of configured peer instances
        
    Example:
        >>> peers = [
        ...     {"host": "pcef.example.com", "port": 3868, "realm": "example.com"},
        ...     {"host": "ocs.example.com", "port": 3868, "realm": "example.com"}
        ... ]
        >>> added_peers = add_peers(node, peers)
    """
    if node.tcp_port:
        return [node.add_peer(f"aaa://{peer['host']}:{peer['port']};transport=tcp",
                          peer['realm'],
                          ip_addresses=peer.get('ip_addresses', ["127.0.0.1"]),
                          is_persistent=peer.get('is_persistent', True),
                          is_default=peer.get('is_default', False))
            for peer in peers_list]
    elif node.sctp_port:
        return [node.add_peer(f"aaa://{peer['host']}:{peer['port']};transport=sctp",
                          peer['realm'],
                          ip_addresses=peer['ip_addresses'],
                          is_persistent=peer.get('is_persistent', True),
                          is_default=peer.get('is_default', False))
            for peer in peers_list]

def add_peer_to_node(node: Node, host: str, realm: str, port: int, ip_addresses: List[str] = ["127.0.0.1"], initiate_connection: bool = True) -> Peer:
    """
    Add a single peer to a Diameter node.
    
    This function adds a single peer to a Diameter node with the specified
    configuration. It automatically handles the transport protocol (TCP or SCTP)
    based on the node's configuration.
    
    Args:
        node (Node): The Diameter node to add the peer to
        host (str): Peer hostname
        realm (str): Peer realm name
        port (int): Peer port number
        ip_addresses (List[str], optional): List of peer IP addresses. Defaults to ["127.0.0.1"]
        initiate_connection (bool, optional): Whether to initiate connection. Defaults to True
        
    Returns:
        Peer: The configured peer instance
        
    Example:
        >>> peer = add_peer_to_node(node, "pcef.example.com", "example.com", 3868)
    """
    if node.tcp_port:
        peer = node.add_peer(f"aaa://{host}:{port};transport=tcp", realm, ip_addresses=ip_addresses, is_persistent=initiate_connection)
    elif node.sctp_port:
        peer = node.add_peer(f"aaa://{host}:{port};transport=sctp", realm, ip_addresses=ip_addresses, is_persistent=initiate_connection)
    return peer
