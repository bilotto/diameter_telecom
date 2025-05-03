from typing import List, Dict
from diameter.node import Node
from diameter.node.node import Peer

def create_node(origin_host: str,
                realm_name: str,
                ip_addresses: List[str],
                port: int,
                sctp: bool = False,
                vendor_ids=[]) -> Node:
    if not sctp:
        node = Node(origin_host, realm_name, ip_addresses=ip_addresses, tcp_port=port, vendor_ids=vendor_ids)
    else:
        node = Node(origin_host, realm_name, ip_addresses=ip_addresses, sctp_port=port, vendor_ids=vendor_ids)
    return node

def add_peers(node: Node, peers_list: List[Dict]) -> List[Peer]:
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


def create_peer_uri(node: Node) -> str:
    if node.tcp_port:
        return f"aaa://{node.origin_host}:{node.tcp_port};transport=tcp"
    elif node.sctp_port:
        return f"aaa://{node.origin_host}:{node.sctp_port};transport=sctp"

