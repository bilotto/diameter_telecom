from ..diameter.helpers import create_node
from ..carrier import Carrier
from diameter.message.constants import *

class DiameterEntity:
    def __init__(self, origin_host, origin_realm, ip_addresses, port, sctp=False, vendor_ids=[VENDOR_ETSI, VENDOR_TGPP, VENDOR_TGPP2]):
        self.node = create_node(origin_host, origin_realm, ip_addresses, port, sctp, vendor_ids)
        self.carrier: Carrier = None

    def start(self):
        self.node.start()
        for app in self.node.applications:
            app.wait_for_ready()

    def set_carrier(self, carrier: Carrier):
        self.carrier = carrier