from ..diameter.helpers import create_node

class DiameterEntity:
    def __init__(self, origin_host, origin_realm, ip_addresses, port, sctp, vendor_ids):
        self.node = create_node(origin_host, origin_realm, ip_addresses, port, sctp, vendor_ids)

    def start(self):
        self.node.start()