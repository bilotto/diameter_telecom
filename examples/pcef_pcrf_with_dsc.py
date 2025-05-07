import logging
logging.basicConfig(level=logging.DEBUG)

from diameter_telecom.entities_3gpp import PCRF, PCEF
from diameter_telecom.entities_3gpp.dsc import DSC

pcrf = PCRF(origin_host="pcrf", realm_name="realm", ip_addresses=["127.0.0.1"], tcp_port=3868, vendor_ids=[10415,])
pcef = PCEF(origin_host="pcef", realm_name="realm", ip_addresses=["127.0.0.1"], tcp_port=3869, vendor_ids=[10415,])

dsc = DSC(origin_host="dsc", realm_name="realm", ip_addresses=["127.0.0.1"], tcp_port=3870, vendor_ids=[10415,])

pcrf.add_peer(dsc, initiate_connection=False)
pcef.add_peer(dsc, initiate_connection=False)

dsc.add_peer(pcrf, initiate_connection=True)
dsc.add_peer(pcef, initiate_connection=True)

pcrf.start()
pcef.start()
dsc.start()

pcrf.wait_for_ready()
pcef.wait_for_ready()
dsc.wait_for_ready()
