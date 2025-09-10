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

# Access sessions through SessionManager
print("PCEF Gx Sessions:", pcef_service.gx_app.session_manager.sessions[APP_3GPP_GX])
print("PCRF Gx Sessions:", pcrf_service.gx_app.session_manager.sessions[APP_3GPP_GX])

# Show session details
for session_id, session in pcef_service.gx_app.session_manager.sessions[APP_3GPP_GX].items():
    print(f"PCEF Session {session_id}:")
    print(f"  - Active: {session.active}")
    print(f"  - Subscriber: {session.subscriber}")
    print(f"  - Messages: {len(session.messages)}")
    if hasattr(session, 'framed_ip_address') and session.framed_ip_address:
        print(f"  - Framed IP: {session.framed_ip_address}")

# Show all messages processed by SessionManager
print(f"Total messages processed by PCEF SessionManager: {len(pcef_service.gx_app.session_manager.messages)}")
print(f"Total subscribers in PCEF SessionManager: {len(pcef_service.gx_app.session_manager.subscribers.subscribers)}")





# pcef_service.stop()
# pcrf_service.stop()