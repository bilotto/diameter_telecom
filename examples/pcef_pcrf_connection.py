import logging

# Configure logging for the example
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# Set library component log levels
logging.getLogger("diameter_telecom.entities_3gpp.dsc").setLevel(logging.INFO)
logging.getLogger("diameter_telecom.diameter.session_manager").setLevel(logging.INFO)
logging.getLogger("diameter_telecom.services.data").setLevel(logging.INFO)

# Suppress noisy diameter library messages
logging.getLogger("diameter").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)
logger.info("🚀 Starting PCEF-PCRF Connection Example")

from diameter_telecom import *

logger.info("📡 Creating PCEF and PCRF entities...")
pcrf = PCRF(origin_host="pcrf", realm_name="python.realm", ip_addresses=["127.0.0.1"], tcp_port=3868, vendor_ids=[10415,])
pcef = PCEF(origin_host="pcef", realm_name="python.realm", ip_addresses=["127.0.0.1"], tcp_port=3869, vendor_ids=[10415,])

logger.info("🔗 Setting up peer relationships...")
pcrf.add_node_as_peer(pcef.node, app_id=APP_3GPP_GX, initiate_connection=False)
pcef.add_node_as_peer(pcrf.node, app_id=APP_3GPP_GX, initiate_connection=True)

logger.info("⚙️ Setting up Diameter applications...")
pcrf.setup_app(app_id=APP_3GPP_GX, max_threads=1, request_handler=handle_request)
pcef.setup_app(app_id=APP_3GPP_GX, max_threads=1, request_handler=handle_request)

try:
    logger.info("🏁 Starting entities...")
    pcrf.start()
    pcef.start()

    logger.info("⏳ Waiting for entities to be ready...")
    pcrf.wait_for_ready()
    pcef.wait_for_ready()
    logger.info("✅ Entities are ready!")

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
    logger.info("✅ Message exchange completed successfully!")

finally:
    # ===== CLEANUP =====
    logger.info("🧹 Cleaning up entities...")
    pcef.stop()
    pcrf.stop()
    logger.info("✅ Cleanup completed!")

