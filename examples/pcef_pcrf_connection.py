import logging
logging.basicConfig(level=logging.DEBUG)

# logging.getLogger("diameter.node").setLevel(logging.ERROR)
# logging.getLogger("diameter.peer").setLevel(logging.ERROR)
# logging.getLogger("diameter.application").setLevel(logging.ERROR)
# logging.getLogger("diameter.connection").setLevel(logging.ERROR)
# logging.getLogger("diameter.stats").setLevel(logging.ERROR)
# logging.getLogger("diameter.peer.msg").setLevel(logging.ERROR)

logging.getLogger("diameter").setLevel(logging.ERROR)



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

from diameter.message.commands import CreditControlRequest

pcef_service = DataService(pcef)
pcrf_service = DataService(pcrf)

ccr = CreditControlRequest()
ccr.session_id = f"{pcef.gx_app.node.session_generator.next_id()}"
ccr.cc_request_type = E_CC_REQUEST_TYPE_INITIAL_REQUEST
ccr.cc_request_number = 0
ccr.header.application_id = APP_3GPP_GX
diameter_message = DiameterMessage(ccr)

subscriber = Subscriber(msisdn="123456789", imsi="123456789012345")

diameter_message.message.subscription_id = subscriber.subscription_id

request, answer = pcef_service.send_request(diameter_message)

pcef_service.gx_app.sessions
pcrf_service.gx_app.sessions


ccr_i = DiameterMessage(diameter_message.hex_string)


# pcef_service.stop()
# pcrf_service.stop()