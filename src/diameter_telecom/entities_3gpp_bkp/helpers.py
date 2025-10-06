from diameter.node import Node

def node_peer_uri(node: Node):
    if node.tcp_port:
        return f"aaa://{node.origin_host}:{node.tcp_port};transport=tcp"
    elif node.sctp_port:
        return f"aaa://{node.origin_host}:{node.sctp_port};transport=sctp"
    else:
        raise ValueError(f"Node {node.origin_host} has no TCP or SCTP port")


def add_node_as_peer(node: Node, node_peer: Node, app_id: str, initiate_connection: bool = False):
    if app_id not in node.all_peers:
        node.all_peers[app_id] = []
    node.all_peers[app_id].append(node.node.add_peer(node_peer_uri(node_peer), node_peer.realm_name, node_peer.ip_addresses, is_persistent=initiate_connection))

