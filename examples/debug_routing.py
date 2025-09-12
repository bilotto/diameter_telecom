#!/usr/bin/env python3
"""
Minimal Routing Debug Example

This example isolates the exact routing issue by testing:
1. Simple 2-entity setup (like working example)
2. Adding OCS as 3rd entity
3. Using DataService vs direct entity calls
"""

import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# Set specific logger levels
logging.getLogger("diameter_telecom.entities_3gpp.dsc").setLevel(logging.INFO)
logging.getLogger("diameter_telecom.services.data").setLevel(logging.DEBUG)
logging.getLogger("diameter").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

from diameter_telecom import *
from diameter_telecom.diameter.handle_request import handle_request_gx, handle_request_sy
from diameter.message.commands import CreditControlRequest
from diameter.message.constants import E_CC_REQUEST_TYPE_INITIAL_REQUEST
import time

def test_basic_routing():
    """Test basic PCEF->PCRF routing (should work)"""
    logger.info("🧪 TEST 1: Basic PCEF->PCRF routing")
    
    pcef = PCEF(origin_host="pcef", realm_name="test.realm", ip_addresses=["127.0.0.1"], tcp_port=3868, vendor_ids=[10415])
    pcrf = PCRF(origin_host="pcrf", realm_name="test.realm", ip_addresses=["127.0.0.1"], tcp_port=3869, vendor_ids=[10415])
    
    # Peer setup (same as working example)
    pcrf.add_node_as_peer(pcef.node, app_id=APP_3GPP_GX, initiate_connection=False)
    pcef.add_node_as_peer(pcrf.node, app_id=APP_3GPP_GX, initiate_connection=True)
    
    # App setup
    pcef.setup_gx_app(max_threads=1, request_handler=handle_request_gx)
    pcrf.setup_gx_app(max_threads=1, request_handler=handle_request_gx)
    
    try:
        pcef.start()
        pcrf.start()
        pcef.wait_for_ready()
        pcrf.wait_for_ready()
        
        # Test direct DataService call
        logger.info("📡 Testing DataService routing...")
        data_service = DataService(pcef)
        
        ccr = CreditControlRequest()
        ccr.session_id = f"test-basic-{int(time.time())}"
        ccr.cc_request_type = E_CC_REQUEST_TYPE_INITIAL_REQUEST
        ccr.cc_request_number = 0
        ccr.header.application_id = APP_3GPP_GX
        
        diameter_message = DiameterMessage(ccr)
        subscriber = Subscriber(msisdn="123456789", imsi="123456789012345")
        diameter_message.message.subscription_id = subscriber.subscription_id
        
        request, answer = data_service.send_request(diameter_message, timeout=3)
        logger.info("✅ Basic routing successful!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Basic routing failed: {e}")
        return False
    finally:
        pcef.stop()
        pcrf.stop()

def test_three_entity_routing():
    """Test PCEF->PCRF->OCS routing (failing case)"""
    logger.info("🧪 TEST 2: Three-entity routing with OCS")
    
    pcef = PCEF(origin_host="pcef", realm_name="test.realm", ip_addresses=["127.0.0.1"], tcp_port=3868, vendor_ids=[10415])
    pcrf = PCRF(origin_host="pcrf", realm_name="test.realm", ip_addresses=["127.0.0.1"], tcp_port=3869, vendor_ids=[10415])
    ocs = OCS(origin_host="ocs", realm_name="test.realm", ip_addresses=["127.0.0.1"], tcp_port=3870, vendor_ids=[10415])
    
    # Peer setup (comprehensive style)
    pcrf.add_node_as_peer(pcef.node, app_id=APP_3GPP_GX, initiate_connection=False)
    pcef.add_node_as_peer(pcrf.node, app_id=APP_3GPP_GX, initiate_connection=True)
    pcrf.add_node_as_peer(ocs.node, app_id=APP_3GPP_SY, initiate_connection=True)  
    ocs.add_node_as_peer(pcrf.node, app_id=APP_3GPP_SY, initiate_connection=False)
    
    # App setup
    pcef.setup_gx_app(max_threads=1, request_handler=handle_request_gx)
    pcrf.setup_gx_app(max_threads=1, request_handler=handle_request_gx)
    ocs.setup_sy_app(max_threads=1, request_handler=handle_request_sy)
    
    try:
        pcef.start()
        pcrf.start()
        ocs.start()
        pcef.wait_for_ready()
        pcrf.wait_for_ready()
        ocs.wait_for_ready()
        
        # Test DataService with OCS
        logger.info("📡 Testing DataService with OCS routing...")
        data_service = DataService(pcef, ocs)
        
        ccr = CreditControlRequest()
        ccr.session_id = f"test-three-{int(time.time())}"
        ccr.cc_request_type = E_CC_REQUEST_TYPE_INITIAL_REQUEST
        ccr.cc_request_number = 0
        ccr.header.application_id = APP_3GPP_GX
        
        diameter_message = DiameterMessage(ccr)
        subscriber = Subscriber(msisdn="987654321", imsi="987654321012345")
        diameter_message.message.subscription_id = subscriber.subscription_id
        
        request, answer = data_service.send_request(diameter_message, timeout=3)
        logger.info("✅ Three-entity routing successful!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Three-entity routing failed: {e}")
        return False
    finally:
        pcef.stop()
        pcrf.stop()
        ocs.stop()

def main():
    logger.info("🚀 Starting Routing Debug Tests")
    
    # Test 1: Basic routing (should work)
    success1 = test_basic_routing()
    time.sleep(1)  # Brief pause between tests
    
    # Test 2: Three-entity routing (currently failing)
    success2 = test_three_entity_routing()
    
    logger.info("📊 Test Results:")
    logger.info(f"  Basic routing: {'✅ PASS' if success1 else '❌ FAIL'}")
    logger.info(f"  Three-entity routing: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        logger.info("🎉 All routing tests passed!")
    elif success1 and not success2:
        logger.info("🤔 Basic routing works, complex routing fails - issue in multi-entity setup")
    else:
        logger.info("💥 All routing broken - fundamental issue")

if __name__ == "__main__":
    main()
