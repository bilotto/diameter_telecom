import logging
logging.basicConfig(level=logging.DEBUG)

from diameter_telecom import *

pcrf = PCRF(origin_host="pcrf", realm_name="python.realm", ip_addresses=["127.0.0.1"], tcp_port=3868, vendor_ids=[10415,])
pcef = PCEF(origin_host="pcef", realm_name="python.realm", ip_addresses=["127.0.0.1"], tcp_port=3869, vendor_ids=[10415,])

pcrf.add_node_as_peer(pcef, app_id=APP_3GPP_GX, initiate_connection=False)
pcef.add_node_as_peer(pcrf, app_id=APP_3GPP_GX, initiate_connection=True)

pcrf.setup_app(app_id=APP_3GPP_GX, max_threads=1, request_handler=handle_request)
pcef.setup_app(app_id=APP_3GPP_GX, max_threads=1, request_handler=handle_request)

pcrf.start()
pcef.start()

pcrf.wait_for_ready()
pcef.wait_for_ready()

# pcrf.stop()
# pcef.stop()

from diameter.message.commands import CreditControlRequest

ccr = CreditControlRequest()
ccr.session_id = f"{pcef.gx_app.node.session_generator.next_id()}"
ccr.cc_request_type = E_CC_REQUEST_TYPE_INITIAL_REQUEST
ccr.cc_request_number = 0
ccr.header.application_id = APP_3GPP_GX
ccr.auth_application_id = APP_3GPP_GX
diameter_message = DiameterMessage(ccr)

data_service = DataService(pcef)

data_service.send_request(diameter_message)