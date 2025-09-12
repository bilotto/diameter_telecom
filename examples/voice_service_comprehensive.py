#!/usr/bin/env python3
"""
Comprehensive VoiceService Example

This example demonstrates the Services architecture for voice/media sessions.
The VoiceService manages both Gx (policy) and Rx (media) interfaces, showing
how voice calls integrate policy control with media resource management.

Key Features Demonstrated:
- VoiceService composition of PCEF + PCRF + AF entities
- Gx session for data bearer and policy control
- Rx session for media reservation and QoS
- Session binding between Gx and Rx sessions
- Voice call lifecycle (setup, modification, teardown)
- Multiple call scenarios (voice, video, conference)
- Real-world IMS integration patterns
"""

import logging
logging.basicConfig(level=logging.INFO)

# Suppress diameter library noise
logging.getLogger("diameter").setLevel(logging.ERROR)

from diameter_telecom import (
    PCEF, PCRF, AF,
    VoiceService,
    Subscriber, Carrier,
    DiameterMessage,
    APP_3GPP_GX, APP_3GPP_RX,
    handle_request
)
from diameter_telecom.diameter.handle_request import handle_request_gx, handle_request_rx
from diameter_telecom.apn import APN
from diameter_telecom.diameter.session_manager import SessionManager
from diameter.message.commands import CreditControlRequest, AARequest
from diameter.message.constants import (
    E_CC_REQUEST_TYPE_INITIAL_REQUEST, 
    E_CC_REQUEST_TYPE_UPDATE_REQUEST, 
    E_CC_REQUEST_TYPE_TERMINATION_REQUEST
)
import time
import ipaddress


def main():
    print("🎙️ Starting Comprehensive VoiceService Example")
    
    # ===== 1. ENTITY SETUP =====
    print("\n📡 Setting up IMS network entities...")
    
    # Policy and Charging Enforcement Function (in eNodeB/SGW)
    pcef = PCEF(
        origin_host="pcef.ims.net", 
        realm_name="ims.net", 
        ip_addresses=["127.0.0.1"], 
        tcp_port=3868, 
        vendor_ids=[10415]
    )
    
    # Policy and Charging Rules Function (policy server)
    pcrf = PCRF(
        origin_host="pcrf.ims.net", 
        realm_name="ims.net", 
        ip_addresses=["127.0.0.1"], 
        tcp_port=3869, 
        vendor_ids=[10415]
    )
    
    # Application Function (P-CSCF or AS in IMS core)
    af = AF(
        origin_host="pcscf.ims.net", 
        realm_name="ims.net", 
        ip_addresses=["127.0.0.1"], 
        tcp_port=3870, 
        vendor_ids=[10415]
    )
    
    # ===== 2. PEER RELATIONSHIPS =====
    print("🔗 Establishing IMS peer relationships...")
    
    # PCEF-PCRF (Gx interface for policy)
    pcef.add_node_as_peer(pcrf.node, app_id=APP_3GPP_GX, initiate_connection=True)
    pcrf.add_node_as_peer(pcef.node, app_id=APP_3GPP_GX, initiate_connection=False)
    
    # AF-PCRF (Rx interface for media)
    af.add_node_as_peer(pcrf.node, app_id=APP_3GPP_RX, initiate_connection=True)
    pcrf.add_node_as_peer(af.node, app_id=APP_3GPP_RX, initiate_connection=False)
    
    # ===== 3. APPLICATION SETUP =====
    print("⚙️ Setting up IMS applications...")
    
    pcef.setup_gx_app(max_threads=2, request_handler=handle_request_gx)
    pcrf.setup_gx_app(max_threads=2, request_handler=handle_request_gx)
    # Also setup Rx application for AF (required by VoiceService)  
    af.setup_rx_app(max_threads=2, request_handler=handle_request_rx)
    
    # ===== 4. START ENTITIES =====
    print("🏁 Starting IMS entities...")
    pcef.start()
    pcrf.start()
    af.start()
    
    pcef.wait_for_ready()
    pcrf.wait_for_ready()
    af.wait_for_ready()
    
    # ===== 5. CREATE VOICE SERVICE =====
    print("\n🎯 Creating VoiceService...")
    
    voice_service = VoiceService(
        pcef=pcef,
        af=af,
        diameter_config={
            APP_3GPP_GX: {
                'destination_realm': 'ims.net'
            },
            APP_3GPP_RX: {
                'destination_realm': 'ims.net'
            }
        }
    )
    
    # Set unified session manager for Gx-Rx coordination
    session_manager = SessionManager()
    voice_service.set_session_manager(session_manager)
    
    # ===== 6. CREATE IMS SUBSCRIBERS =====
    print("\n👥 Setting up IMS subscribers...")
    
    # IMS carrier
    ims_carrier = Carrier(
        name="IMS-Telecom", 
        mcc_mnc="20201", 
        country_code="30"  # Greece
    )
    
    # IMS APN for voice services
    ims_apn = APN(apn="ims", ip_pool_cidr="10.100.0.0/16")
    ims_carrier.add_apn(ims_apn)
    
    # Create IMS subscribers with different service capabilities
    subscribers = [
        create_ims_subscriber("30693000001", "202010000000001", "alice@ims.net", ["voice"]),
        create_ims_subscriber("30693000002", "202010000000002", "bob@ims.net", ["voice", "video"]),
        create_ims_subscriber("30693000003", "202010000000003", "carol@ims.net", ["voice", "video", "conference"]),
        create_ims_subscriber("30693000004", "202010000000004", "dave@ims.net", ["voice", "sms"]),
        create_ims_subscriber("30693000005", "202010000000005", "eve@ims.net", ["voice", "video", "presence"])
    ]
    
    for subscriber in subscribers:
        ims_carrier.add_subscriber(subscriber)
        subscriber.apn = ims_apn
    
    voice_service.carrier = ims_carrier
    
    # ===== 7. VOICE CALL SCENARIOS =====
    print("\n📞 Running voice call scenarios...")
    
    scenarios = [
        ("📞 Basic Voice Call", subscribers[0], subscribers[1], "voice_call"),
        ("📹 Video Call", subscribers[1], subscribers[2], "video_call"),
        ("👥 Conference Call", subscribers[2], [subscribers[0], subscribers[1]], "conference_call"),
        ("💬 Voice + Messaging", subscribers[3], subscribers[4], "voice_sms"),
        ("🎥 HD Video Call", subscribers[4], subscribers[2], "hd_video_call")
    ]
    
    for scenario_name, caller, called, call_type in scenarios:
        print(f"\n{scenario_name}")
        if isinstance(called, list):
            run_conference_scenario(voice_service, caller, called, call_type)
        else:
            run_call_scenario(voice_service, caller, called, call_type)
        time.sleep(1)  # Brief pause between scenarios
    
    # ===== 8. CLEANUP =====
    print("\n🧹 Cleaning up IMS sessions...")
    voice_service.stop()
    pcef.stop()
    pcrf.stop()
    af.stop()
    
    print("✅ Comprehensive VoiceService example completed!")


def create_ims_subscriber(msisdn: str, imsi: str, sip_uri: str, capabilities: list) -> Subscriber:
    """Create an IMS subscriber with SIP capabilities"""
    subscriber = Subscriber(msisdn=msisdn, imsi=imsi)
    subscriber.sip_uri = sip_uri  # IMS SIP URI
    subscriber.service_capabilities = capabilities  # Voice, video, conference, etc.
    return subscriber


def run_call_scenario(voice_service: VoiceService, caller: Subscriber, called: Subscriber, call_type: str):
    """
    Run a complete voice call scenario with Gx and Rx coordination
    """
    
    # ===== 1. DATA BEARER ESTABLISHMENT (Gx) =====
    print(f"   📡 Establishing data bearer for {caller.msisdn}...")
    
    # Create initial Gx session for data bearer
    gx_session_id = f"gx.{voice_service.pcef.origin_host};{int(time.time())};{caller.msisdn[-6:]}"
    ccr_i = create_gx_bearer_request(voice_service, caller, gx_session_id, call_type)
    
    try:
        gx_request, gx_answer = voice_service.send_request(ccr_i, timeout=3)
        print(f"   ✅ Data bearer established - Session: {gx_session_id[:25]}...")
        
        # Simulate assigned IP address
        caller_ip = "10.100.1.50"  # Would come from CCA response
        
        # ===== 2. MEDIA RESERVATION (Rx) =====
        print(f"   🎙️ Requesting media resources...")
        
        # Create Rx session for media reservation
        rx_session_id = f"rx.{voice_service.af.origin_host};{int(time.time())};{caller.msisdn[-6:]}"
        aar = create_rx_media_request(voice_service, caller, called, rx_session_id, call_type, caller_ip)
        
        try:
            rx_request, rx_answer = voice_service.send_request(aar, timeout=3)
            print(f"   ✅ Media resources reserved - RX Session: {rx_session_id[:25]}...")
            
            # ===== 3. CALL MODIFICATIONS =====
            call_modifications = get_call_modifications(call_type)
            for i, modification in enumerate(call_modifications):
                print(f"   🔄 Call modification: {modification}")
                
                # Update Rx session
                aar_update = create_rx_modification(voice_service, caller, rx_session_id, modification)
                try:
                    rx_mod_req, rx_mod_ans = voice_service.send_request(aar_update, timeout=3)
                    print(f"   ✅ Media modification applied")
                except Exception as e:
                    print(f"   ❌ Media modification failed: {e}")
                
                time.sleep(0.2)  # Brief pause
            
            # ===== 4. CALL TERMINATION =====
            print(f"   📴 Terminating call...")
            
            # Terminate Rx session
            rx_session_term = create_rx_termination(voice_service, rx_session_id)
            try:
                rx_term_req, rx_term_ans = voice_service.send_request(rx_session_term, timeout=3)
                print(f"   ✅ Media resources released")
            except Exception as e:
                print(f"   ❌ Rx termination failed: {e}")
            
            # Terminate Gx session 
            ccr_t = create_gx_termination(voice_service, caller, gx_session_id)
            try:
                gx_term_req, gx_term_ans = voice_service.send_request(ccr_t, timeout=3)
                print(f"   ✅ Data bearer terminated")
            except Exception as e:
                print(f"   ❌ Gx termination failed: {e}")
                
        except Exception as e:
            print(f"   ❌ Media reservation failed: {e}")
            
    except Exception as e:
        print(f"   ❌ Data bearer establishment failed: {e}")


def run_conference_scenario(voice_service: VoiceService, organizer: Subscriber, participants: list, call_type: str):
    """
    Run a conference call scenario with multiple participants
    """
    print(f"   👥 Conference organized by {organizer.msisdn} with {len(participants)} participants")
    
    # For simplicity, just establish organizer's session
    # In real scenario, each participant would have their own Gx/Rx sessions
    run_call_scenario(voice_service, organizer, participants[0], call_type)


def create_gx_bearer_request(voice_service: VoiceService, subscriber: Subscriber, session_id: str, call_type: str) -> DiameterMessage:
    """Create Gx Credit Control Request for data bearer"""
    ccr = CreditControlRequest()
    ccr.session_id = session_id
    ccr.cc_request_type = E_CC_REQUEST_TYPE_INITIAL_REQUEST
    ccr.cc_request_number = 0
    ccr.header.application_id = APP_3GPP_GX
    
    diameter_message = DiameterMessage(ccr)
    diameter_message.message.subscription_id = subscriber.subscription_id
    
    # Could add QoS requirements based on call_type
    return diameter_message


def create_rx_media_request(voice_service: VoiceService, caller: Subscriber, called: Subscriber, 
                           session_id: str, call_type: str, framed_ip: str) -> DiameterMessage:
    """Create Rx AA Request for media reservation"""
    aar = AARequest()
    aar.session_id = session_id
    aar.header.application_id = APP_3GPP_RX
    
    diameter_message = DiameterMessage(aar)
    
    # Add media-specific AVPs based on call type
    media_specs = get_media_specifications(call_type)
    
    # Would add Media-Component-Description AVPs here
    # For now, just basic setup
    return diameter_message


def create_rx_modification(voice_service: VoiceService, subscriber: Subscriber, session_id: str, modification: str) -> DiameterMessage:
    """Create Rx modification request"""
    aar = AARequest()
    aar.session_id = session_id
    aar.header.application_id = APP_3GPP_RX
    
    return DiameterMessage(aar)


def create_rx_termination(voice_service: VoiceService, session_id: str) -> DiameterMessage:
    """Create Rx session termination request"""
    aar = AARequest()
    aar.session_id = session_id
    aar.header.application_id = APP_3GPP_RX
    
    # Would set termination cause
    return DiameterMessage(aar)


def create_gx_termination(voice_service: VoiceService, subscriber: Subscriber, session_id: str) -> DiameterMessage:
    """Create Gx termination request"""
    ccr = CreditControlRequest()
    ccr.session_id = session_id
    ccr.cc_request_type = E_CC_REQUEST_TYPE_TERMINATION_REQUEST
    ccr.cc_request_number = 1  # Termination
    ccr.header.application_id = APP_3GPP_GX
    
    diameter_message = DiameterMessage(ccr)
    diameter_message.message.subscription_id = subscriber.subscription_id
    
    return diameter_message


def get_media_specifications(call_type: str) -> dict:
    """Return media specifications for different call types"""
    specs = {
        "voice_call": {
            "codecs": ["AMR", "AMR-WB"],
            "bandwidth": "12.2 kbps",
            "latency": "< 150ms"
        },
        "video_call": {
            "codecs": ["AMR", "H.264"],
            "bandwidth": "384 kbps",
            "latency": "< 150ms"
        },
        "hd_video_call": {
            "codecs": ["AMR-WB", "H.264"],
            "bandwidth": "768 kbps", 
            "latency": "< 100ms"
        },
        "conference_call": {
            "codecs": ["AMR", "H.264"],
            "bandwidth": "256 kbps",
            "latency": "< 200ms"
        },
        "voice_sms": {
            "codecs": ["AMR"],
            "bandwidth": "12.2 kbps",
            "latency": "< 150ms"
        }
    }
    return specs.get(call_type, specs["voice_call"])


def get_call_modifications(call_type: str) -> list:
    """Return typical call modifications for different call types"""
    modifications = {
        "voice_call": ["codec_change"],
        "video_call": ["add_video", "codec_change"],
        "hd_video_call": ["resolution_upgrade", "codec_optimization"],
        "conference_call": ["add_participant", "mute_control"],
        "voice_sms": ["add_messaging"]
    }
    return modifications.get(call_type, [])


if __name__ == "__main__":
    main()
