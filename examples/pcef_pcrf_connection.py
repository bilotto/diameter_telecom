import logging
logging.basicConfig(level=logging.DEBUG)

from diameter_telecom.entities_3gpp import PCRF, PCEF

pcrf = PCRF(origin_host="pcrf", realm_name="realm", ip_addresses=["127.0.0.1"], tcp_port=3868, vendor_ids=[10415,])
pcef = PCEF(origin_host="pcef", realm_name="realm", ip_addresses=["127.0.0.1"], tcp_port=3869, vendor_ids=[10415,])

pcrf.add_peer(pcef, initiate_connection=False)
pcef.add_peer(pcrf, initiate_connection=True)

pcrf.start()
pcef.start()
