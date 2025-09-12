import logging
logging.basicConfig(level=logging.DEBUG)

from diameter_telecom.entities_3gpp import PCRF, PCEF
from diameter_telecom.entities_3gpp.dsc import DSC
from diameter_telecom.diameter.constants import APP_3GPP_GX

pcrf = PCRF(origin_host="pcrf", realm_name="realm", ip_addresses=["127.0.0.1"], tcp_port=3868, vendor_ids=[10415,])
pcef = PCEF(origin_host="pcef", realm_name="realm", ip_addresses=["127.0.0.1"], tcp_port=3869, vendor_ids=[10415,])

dsc = DSC(origin_host="dsc", realm_name="realm", ip_addresses=["127.0.0.1"], tcp_port=3870, vendor_ids=[10415,])

pcrf.add_node_as_peer(dsc.node, app_id=APP_3GPP_GX, initiate_connection=False)
pcef.add_node_as_peer(dsc.node, app_id=APP_3GPP_GX, initiate_connection=False)

dsc.add_node_as_peer(pcrf.node, app_id=APP_3GPP_GX, initiate_connection=True)
dsc.add_node_as_peer(pcef.node, app_id=APP_3GPP_GX, initiate_connection=True)

# Setup applications before starting
from diameter_telecom.diameter.handle_request import handle_request
pcrf.setup_gx_app(max_threads=1, request_handler=handle_request)
pcef.setup_gx_app(max_threads=1, request_handler=handle_request)
dsc.setup_gx_app(max_threads=1, request_handler=handle_request)

pcrf.start()
pcef.start()
dsc.start()

pcrf.wait_for_ready()
pcef.wait_for_ready()
dsc.wait_for_ready()

pcrf.stop()
pcef.stop()
dsc.stop()