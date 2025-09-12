#!/usr/bin/env python3
"""
Comprehensive DataService Example

This example demonstrates the proper use of the Services architecture for data sessions.
The DataService provides a high-level abstraction over PCEF, PCRF, and OCS entities,
handling Gx (policy) and Sy (charging) message flows automatically.

Key Features Demonstrated:
- DataService composition of multiple entities (PCEF + PCRF + OCS)
- Multiple subscribers with different APNs and service plans
- Complete session lifecycle (Initial, Update, Termination)
- Automatic session management and binding
- Unified message sending API
- Multiple carriers and service offerings
"""

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
logging.getLogger("diameter_telecom.services.service").setLevel(logging.INFO)
logging.getLogger("diameter_telecom.services.data").setLevel(logging.INFO)
logging.getLogger("diameter_telecom.diameter.message_processing_pipeline").setLevel(logging.DEBUG)

# ENABLE ALL DIAMETER LIBRARY LOGGING FOR DEBUG
logging.getLogger("diameter").setLevel(logging.DEBUG)
logging.getLogger("diameter.node").setLevel(logging.DEBUG)
logging.getLogger("diameter.peer").setLevel(logging.DEBUG)
logging.getLogger("diameter.application").setLevel(logging.DEBUG)
logging.getLogger("diameter.connection").setLevel(logging.DEBUG)
logging.getLogger("diameter.stats").setLevel(logging.DEBUG)
logging.getLogger("diameter.peer.msg").setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

from diameter_telecom import (
    PCEF, PCRF, OCS, 
    DataService,
    Subscriber, Carrier,
    DiameterMessage,
    APP_3GPP_GX, APP_3GPP_SY,
    handle_request
)
from diameter_telecom.entities_3gpp.dsc import DSC
from diameter_telecom.diameter.handle_request import handle_request_gx, handle_request_sy
from diameter_telecom.apn import APN
from diameter_telecom.diameter.session_manager import SessionManager
from diameter.message.commands import CreditControlRequest
from diameter.message.constants import E_CC_REQUEST_TYPE_INITIAL_REQUEST, E_CC_REQUEST_TYPE_UPDATE_REQUEST, E_CC_REQUEST_TYPE_TERMINATION_REQUEST
import time


def main():
    logger.info("🚀 Starting Comprehensive DataService Example")
    
    # ===== 1. ENTITY SETUP =====
    logger.info("📡 Setting up Diameter entities...")
    
    # Create network entities with proper configuration - SIMPLIFIED HOSTS
    pcef = PCEF(
        origin_host="pcef", 
        realm_name="mobile.net", 
        ip_addresses=["127.0.0.1"], 
        tcp_port=3868, 
        vendor_ids=[10415]  # 3GPP vendor ID
    )
    
    pcrf = PCRF(
        origin_host="pcrf", 
        realm_name="mobile.net", 
        ip_addresses=["127.0.0.1"], 
        tcp_port=3869, 
        vendor_ids=[10415]
    )
    
    ocs = OCS(
        origin_host="ocs", 
        realm_name="mobile.net", 
        ip_addresses=["127.0.0.1"], 
        tcp_port=3870, 
        vendor_ids=[10415]
    )
    
    # DSC as routing hub
    dsc = DSC(
        origin_host="dsc", 
        realm_name="mobile.net", 
        ip_addresses=["127.0.0.1"], 
        tcp_port=3871, 
        vendor_ids=[10415]
    )
    
    # ===== 2. PEER RELATIONSHIPS =====
    logger.info("🔗 Establishing DSC-based peer relationships...")
    
    # PCEF connects to DSC (Gx interface)
    pcef.add_node_as_peer(dsc.node, app_id=APP_3GPP_GX, initiate_connection=True)
    dsc.add_node_as_peer(pcef.node, app_id=APP_3GPP_GX, initiate_connection=False)
    
    # PCRF connects to DSC (Gx interface) 
    pcrf.add_node_as_peer(dsc.node, app_id=APP_3GPP_GX, initiate_connection=True)
    dsc.add_node_as_peer(pcrf.node, app_id=APP_3GPP_GX, initiate_connection=False)
    
    # PCRF connects to DSC (Sy interface) - NEEDED for SLR to OCS
    pcrf.add_node_as_peer(dsc.node, app_id=APP_3GPP_SY, initiate_connection=True)
    dsc.add_node_as_peer(pcrf.node, app_id=APP_3GPP_SY, initiate_connection=False)
    
    # OCS connects to DSC (Sy interface)
    ocs.add_node_as_peer(dsc.node, app_id=APP_3GPP_SY, initiate_connection=True)
    dsc.add_node_as_peer(ocs.node, app_id=APP_3GPP_SY, initiate_connection=False)
    
    # ===== 3. APPLICATION SETUP =====
    logger.info("⚙️ Setting up Diameter applications...")
    
    # Setup applications with proper request handlers
    pcef.setup_gx_app(max_threads=2, request_handler=handle_request_gx)
    
    # PCRF needs BOTH Gx (receive CCR) AND Sy (send SLR to OCS) for proper 3GPP flow
    pcrf.setup_gx_app(max_threads=2, request_handler=handle_request_gx)
    pcrf.setup_sy_app(max_threads=2, request_handler=handle_request_sy)
    
    ocs.setup_sy_app(max_threads=2, request_handler=handle_request_sy)
    
    # DSC needs both Gx and Sy for routing
    from diameter_telecom.entities_3gpp.dsc import handle_request_dsc
    dsc.setup_gx_app(max_threads=3, request_handler=handle_request_dsc)
    dsc.setup_sy_app(max_threads=3, request_handler=handle_request_dsc)
    
    # ===== 4. START ENTITIES =====
    logger.info("🏁 Starting entities...")
    
    # START DSC FIRST - it needs to be listening before others connect
    logger.info("🌐 Starting DSC routing hub first...")
    dsc.start()
    dsc.wait_for_ready()
    logger.info("✅ DSC ready, now starting other entities...")
    
    # Now start other entities that will connect to DSC
    pcef.start()
    pcrf.start()
    ocs.start()
    
    # Wait for all to be ready
    pcef.wait_for_ready()
    pcrf.wait_for_ready()
    ocs.wait_for_ready()
    
    # ===== 5. CREATE DATA SERVICE =====
    logger.info("🎯 Creating DataService...")
    
    data_service = DataService(
        pcef=pcef,
        ocs=ocs,
        diameter_config={
            APP_3GPP_GX: {
                'destination_realm': 'mobile.net'
            }
        }
    )
    
    # Set unified session manager
    session_manager = SessionManager()
    data_service.set_session_manager(session_manager)
    
    # ===== 6. CREATE CARRIERS AND SUBSCRIBERS =====
    logger.info("👥 Setting up carriers and subscribers...")
    
    # Create mobile carrier
    mobile_carrier = Carrier(
        name="MobileNet", 
        mcc_mnc="31026", 
        country_code="31"  # Netherlands
    )
    
    # Create APNs for different services
    internet_apn = APN(apn="internet", ip_pool_cidr="10.10.0.0/16")
    premium_apn = APN(apn="premium", ip_pool_cidr="10.20.0.0/16") 
    iot_apn = APN(apn="iot", ip_pool_cidr="172.16.0.0/24")
    
    mobile_carrier.add_apn(internet_apn)
    mobile_carrier.add_apn(premium_apn)
    mobile_carrier.add_apn(iot_apn)
    
    # Create diverse subscribers
    subscribers = [
        Subscriber(msisdn="31612345001", imsi="310260000000001"),  # Regular user
        Subscriber(msisdn="31612345002", imsi="310260000000002"),  # Premium user  
        Subscriber(msisdn="31612345003", imsi="310260000000003"),  # IoT device
        Subscriber(msisdn="31612345004", imsi="310260000000004"),  # Heavy user
        Subscriber(msisdn="31612345005", imsi="310260000000005"),  # Roaming user
    ]
    
    # Assign subscribers to carrier and APNs
    for i, subscriber in enumerate(subscribers):
        mobile_carrier.add_subscriber(subscriber)
        if i == 1:  # Premium user
            subscriber.apn = premium_apn
        elif i == 2:  # IoT device
            subscriber.apn = iot_apn
        else:  # Regular users
            subscriber.apn = internet_apn
    
    data_service.carrier = mobile_carrier
    
    # ===== 7. SESSION SCENARIOS =====
    logger.info("💫 Running session scenarios...")
    
    scenarios = [
        ("📱 Regular Data Session", subscribers[0], "normal_usage"),
        ("🏆 Premium User Session", subscribers[1], "premium_usage"), 
        ("🔌 IoT Device Session", subscribers[2], "iot_usage"),
        ("🌊 Heavy Usage Session", subscribers[3], "heavy_usage"),
        ("🌍 Roaming Session", subscribers[4], "roaming_usage")
    ]
    
    for scenario_name, subscriber, usage_type in scenarios:
        logger.info(f"\n{scenario_name}")
        run_session_scenario(data_service, subscriber, usage_type)
        time.sleep(0.5)  # Brief pause between scenarios
    
    # ===== 8. CLEANUP =====
    logger.info("🧹 Cleaning up...")
    data_service.stop()
    pcef.stop()
    pcrf.stop() 
    ocs.stop()
    dsc.stop()  # Stop DSC routing hub
    
    logger.info("✅ Comprehensive DataService example completed!")


def run_session_scenario(data_service: DataService, subscriber: Subscriber, usage_type: str):
    """
    Run a complete session scenario: Initial -> Updates -> Termination
    """
    
    # ===== INITIAL REQUEST =====
    ccr_i = create_ccr_message(data_service, subscriber, E_CC_REQUEST_TYPE_INITIAL_REQUEST, 0)
    logger.info(f"   🟢 Sending CCR-I for {subscriber.msisdn}...")
    
    try:
        request_i, answer_i = data_service.send_request(ccr_i, timeout=3)
        logger.info(f"   ✅ CCR-I successful - Session: {ccr_i.session_id[:20]}...")
        
        # ===== UPDATE REQUESTS =====  
        usage_patterns = get_usage_pattern(usage_type)
        for i, update_reason in enumerate(usage_patterns):
            ccr_u = create_ccr_message(
                data_service, subscriber, 
                E_CC_REQUEST_TYPE_UPDATE_REQUEST, 
                i + 1, 
                session_id=ccr_i.session_id,
                update_reason=update_reason
            )
            logger.info(f"   🔄 Sending CCR-U #{i+1} ({update_reason})...")
            
            try:
                request_u, answer_u = data_service.send_request(ccr_u, timeout=3)
                logger.info(f"   ✅ CCR-U #{i+1} successful")
            except Exception as e:
                logger.error(f"   ❌ CCR-U #{i+1} failed: {e}")
        
        # ===== TERMINATION REQUEST =====
        ccr_t = create_ccr_message(
            data_service, subscriber, 
            E_CC_REQUEST_TYPE_TERMINATION_REQUEST, 
            len(usage_patterns) + 1, 
            session_id=ccr_i.session_id
        )
        logger.info(f"   🔴 Sending CCR-T...")
        
        try:
            request_t, answer_t = data_service.send_request(ccr_t, timeout=3)
            logger.info(f"   ✅ CCR-T successful - Session terminated")
        except Exception as e:
            logger.error(f"   ❌ CCR-T failed: {e}")
            
    except Exception as e:
        logger.error(f"   ❌ CCR-I failed: {e}")


def create_ccr_message(data_service: DataService, subscriber: Subscriber, 
                      request_type: int, request_number: int, 
                      session_id: str = None, update_reason: str = None) -> DiameterMessage:
    """
    Create a Credit Control Request with proper subscriber information
    """
    ccr = CreditControlRequest()
    
    # Session management
    if session_id:
        ccr.session_id = session_id
    else:
        ccr.session_id = f"{data_service.pcef.origin_host};{int(time.time())};{subscriber.msisdn[-6:]};{request_number}"
    
    # Request details
    ccr.cc_request_type = request_type
    ccr.cc_request_number = request_number
    ccr.header.application_id = APP_3GPP_GX
    
    # Create diameter message wrapper
    diameter_message = DiameterMessage(ccr)
    diameter_message.message.subscription_id = subscriber.subscription_id
    
    # Add additional AVPs based on request type and usage pattern
    if update_reason:
        # Could add usage reporting, QoS changes, etc.
        pass
    
    return diameter_message


def get_usage_pattern(usage_type: str) -> list:
    """
    Return appropriate update patterns for different usage types
    """
    patterns = {
        "normal_usage": ["quota_threshold", "time_limit"],
        "premium_usage": ["quota_threshold", "qos_upgrade", "time_limit"], 
        "iot_usage": ["periodic_report"],
        "heavy_usage": ["quota_threshold", "quota_threshold", "fair_usage_policy", "time_limit"],
        "roaming_usage": ["roaming_tariff", "quota_threshold", "time_limit"]
    }
    return patterns.get(usage_type, ["quota_threshold", "time_limit"])


if __name__ == "__main__":
    main()
