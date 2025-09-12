#!/usr/bin/env python3
"""
Advanced Multi-Service Example

This example demonstrates the complete Services architecture with multiple
carriers, subscribers, and service types operating concurrently. It shows
real-world telecom scenarios with data and voice services running in parallel.

Key Features Demonstrated:
- Multiple carriers with different service offerings
- Concurrent DataService and VoiceService operations
- Complex subscriber scenarios (roaming, family plans, enterprise)
- Service coordination and session binding
- Advanced session management patterns
- Performance monitoring and reporting
- Realistic telecom business logic
"""

import logging
import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger("diameter").setLevel(logging.ERROR)

from diameter_telecom import (
    PCEF, PCRF, OCS, AF,
    DataService, VoiceService, 
    Subscriber, Carrier,
    DiameterMessage,
    SessionManager,
    APP_3GPP_GX,
    handle_request
)
from diameter_telecom.diameter.handle_request import handle_request_gx, handle_request_rx, handle_request_sy
from diameter_telecom.apn import APN


class TelecomNetwork:
    """
    Represents a complete telecom network with multiple services
    """
    
    def __init__(self, name: str):
        self.name = name
        self.entities = {}
        self.services = {}
        self.carriers = []
        self.session_manager = SessionManager()
        self.active_sessions = {}
        self.performance_stats = {
            'total_sessions': 0,
            'successful_sessions': 0,
            'failed_sessions': 0,
            'active_data_sessions': 0,
            'active_voice_sessions': 0
        }
    
    def setup_infrastructure(self):
        """Setup network entities and services"""
        print(f"🏗️ Setting up {self.name} infrastructure...")
        
        # Create core network entities
        self.entities['pcef'] = PCEF(
            origin_host=f"pcef.{self.name.lower()}.net",
            realm_name=f"{self.name.lower()}.net", 
            ip_addresses=["127.0.0.1"],
            tcp_port=3868,
            vendor_ids=[10415]
        )
        
        self.entities['pcrf'] = PCRF(
            origin_host=f"pcrf.{self.name.lower()}.net",
            realm_name=f"{self.name.lower()}.net",
            ip_addresses=["127.0.0.1"], 
            tcp_port=3869,
            vendor_ids=[10415]
        )
        
        self.entities['ocs'] = OCS(
            origin_host=f"ocs.{self.name.lower()}.net",
            realm_name=f"{self.name.lower()}.net",
            ip_addresses=["127.0.0.1"],
            tcp_port=3870,
            vendor_ids=[10415]
        )
        
        self.entities['af'] = AF(
            origin_host=f"af.{self.name.lower()}.net",
            realm_name=f"{self.name.lower()}.net",
            ip_addresses=["127.0.0.1"],
            tcp_port=3871,
            vendor_ids=[10415]
        )
        
        # Setup peer relationships
        self._setup_peer_relationships()
        
        # Setup applications
        self._setup_applications()
        
        # Start entities
        self._start_entities()
        
        # Create services
        self._create_services()
    
    def _setup_peer_relationships(self):
        """Setup diameter peer relationships between entities"""
        pcef, pcrf, ocs, af = self.entities['pcef'], self.entities['pcrf'], self.entities['ocs'], self.entities['af']
        
        # Gx: PCEF <-> PCRF
        pcef.add_node_as_peer(pcrf.node, app_id=APP_3GPP_GX, initiate_connection=True)
        pcrf.add_node_as_peer(pcef.node, app_id=APP_3GPP_GX, initiate_connection=False)
        
        # Could add Sy: PCRF <-> OCS and Rx: AF <-> PCRF relationships here
        
    def _setup_applications(self):
        """Setup diameter applications with proper request handlers"""
        # Setup Gx applications for all entities that support it
        for entity in self.entities.values():
            if hasattr(entity, 'setup_gx_app'):
                entity.setup_gx_app(max_threads=3, request_handler=handle_request_gx)
        
        # Setup Sy application for OCS (required by DataService)
        self.entities['ocs'].setup_sy_app(max_threads=3, request_handler=handle_request_sy)
        
        # Setup Rx application for AF (required by VoiceService)
        self.entities['af'].setup_rx_app(max_threads=3, request_handler=handle_request_rx)
    
    def _start_entities(self):
        """Start all diameter entities"""
        for name, entity in self.entities.items():
            print(f"   🚀 Starting {name.upper()}...")
            entity.start()
        
        for entity in self.entities.values():
            entity.wait_for_ready()
    
    def _create_services(self):
        """Create high-level services"""
        self.services['data'] = DataService(
            pcef=self.entities['pcef'],
            ocs=self.entities['ocs'],
            diameter_config={APP_3GPP_GX: {'destination_realm': f'{self.name.lower()}.net'}}
        )
        
        self.services['voice'] = VoiceService(
            pcef=self.entities['pcef'],
            af=self.entities['af'],
            diameter_config={APP_3GPP_GX: {'destination_realm': f'{self.name.lower()}.net'}}
        )
        
        # Set unified session manager
        for service in self.services.values():
            service.set_session_manager(self.session_manager)
    
    def add_carrier(self, carrier: Carrier):
        """Add a carrier to the network"""
        self.carriers.append(carrier)
        for service in self.services.values():
            service.carrier = carrier  # Last carrier wins for simplicity
    
    def simulate_subscriber_activity(self, duration_seconds: int = 60):
        """
        Simulate realistic subscriber activity across multiple services
        """
        print(f"📊 Starting {duration_seconds}s activity simulation...")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            while time.time() - start_time < duration_seconds:
                # Randomly choose activity type
                activity_type = random.choices(
                    ['data_session', 'voice_call', 'video_call', 'idle'],
                    weights=[40, 30, 20, 10]
                )[0]
                
                if activity_type != 'idle':
                    # Pick random subscriber
                    all_subscribers = []
                    for carrier in self.carriers:
                        all_subscribers.extend(carrier.subscribers)
                    
                    if all_subscribers:
                        subscriber = random.choice(all_subscribers)
                        future = executor.submit(self._handle_subscriber_activity, subscriber, activity_type)
                        futures.append(future)
                
                # Random delay between activities
                time.sleep(random.uniform(0.5, 3.0))
            
            # Wait for all activities to complete
            for future in futures:
                try:
                    future.result(timeout=10)
                except Exception as e:
                    print(f"   ❌ Activity failed: {e}")
                    self.performance_stats['failed_sessions'] += 1
        
        self._print_performance_report()
    
    def _handle_subscriber_activity(self, subscriber: Subscriber, activity_type: str):
        """Handle individual subscriber activity"""
        self.performance_stats['total_sessions'] += 1
        
        try:
            if activity_type == 'data_session':
                self._simulate_data_session(subscriber)
                self.performance_stats['active_data_sessions'] += 1
            elif activity_type in ['voice_call', 'video_call']:
                self._simulate_voice_session(subscriber, activity_type)
                self.performance_stats['active_voice_sessions'] += 1
            
            self.performance_stats['successful_sessions'] += 1
            
        except Exception as e:
            print(f"   ❌ {activity_type} failed for {subscriber.msisdn}: {e}")
            self.performance_stats['failed_sessions'] += 1
    
    def _simulate_data_session(self, subscriber: Subscriber):
        """Simulate a data session scenario"""
        from diameter.message.commands import CreditControlRequest
        from diameter.message.constants import E_CC_REQUEST_TYPE_INITIAL_REQUEST, E_CC_REQUEST_TYPE_TERMINATION_REQUEST
        
        # Create session
        session_id = f"data.{int(time.time())}.{subscriber.msisdn[-6:]}"
        
        # Initial request
        ccr_i = CreditControlRequest()
        ccr_i.session_id = session_id
        ccr_i.cc_request_type = E_CC_REQUEST_TYPE_INITIAL_REQUEST
        ccr_i.cc_request_number = 0
        ccr_i.header.application_id = APP_3GPP_GX
        
        dm_i = DiameterMessage(ccr_i)
        dm_i.message.subscription_id = subscriber.subscription_id
        
        # Send request
        req, ans = self.services['data'].send_request(dm_i, timeout=2)
        print(f"   📱 Data session started for {subscriber.msisdn}")
        
        # Simulate some usage
        time.sleep(random.uniform(1, 5))
        
        # Termination request
        ccr_t = CreditControlRequest()
        ccr_t.session_id = session_id
        ccr_t.cc_request_type = E_CC_REQUEST_TYPE_TERMINATION_REQUEST
        ccr_t.cc_request_number = 1
        ccr_t.header.application_id = APP_3GPP_GX
        
        dm_t = DiameterMessage(ccr_t)
        dm_t.message.subscription_id = subscriber.subscription_id
        
        req_t, ans_t = self.services['data'].send_request(dm_t, timeout=2)
        print(f"   📱 Data session ended for {subscriber.msisdn}")
    
    def _simulate_voice_session(self, subscriber: Subscriber, call_type: str):
        """Simulate a voice/video call scenario"""
        print(f"   📞 {call_type} started for {subscriber.msisdn}")
        
        # Simulate call duration
        call_duration = random.uniform(30, 180)  # 30s to 3 minutes
        time.sleep(min(call_duration / 10, 2))  # Accelerated for demo
        
        print(f"   📞 {call_type} ended for {subscriber.msisdn}")
    
    def _print_performance_report(self):
        """Print network performance statistics"""
        stats = self.performance_stats
        success_rate = (stats['successful_sessions'] / max(stats['total_sessions'], 1)) * 100
        
        print(f"\n📈 {self.name} Performance Report:")
        print(f"   Total Sessions: {stats['total_sessions']}")
        print(f"   Successful: {stats['successful_sessions']}")
        print(f"   Failed: {stats['failed_sessions']}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Peak Data Sessions: {stats['active_data_sessions']}")
        print(f"   Peak Voice Sessions: {stats['active_voice_sessions']}")
    
    def shutdown(self):
        """Gracefully shutdown the network"""
        print(f"🔌 Shutting down {self.name} network...")
        for service in self.services.values():
            service.stop()


def create_test_carriers() -> List[Carrier]:
    """Create diverse carriers for testing"""
    
    # European Carrier
    eu_carrier = Carrier(name="EuroMobile", mcc_mnc="26207", country_code="49")
    eu_carrier.add_apn(APN(apn="internet", ip_pool_cidr="10.0.0.0/16"))
    eu_carrier.add_apn(APN(apn="ims", ip_pool_cidr="10.1.0.0/16"))
    
    # Add European subscribers
    for i in range(1, 21):  # 20 subscribers
        subscriber = Subscriber(
            msisdn=f"49151000{i:04d}", 
            imsi=f"26207000000{i:05d}"
        )
        subscriber.apn = eu_carrier.apns[0] if i % 2 == 0 else eu_carrier.apns[1]
        eu_carrier.add_subscriber(subscriber)
    
    # American Carrier
    us_carrier = Carrier(name="USATel", mcc_mnc="31026", country_code="1")
    us_carrier.add_apn(APN(apn="vzwinternet", ip_pool_cidr="192.168.0.0/16"))
    us_carrier.add_apn(APN(apn="vzwims", ip_pool_cidr="172.16.0.0/16"))
    
    # Add American subscribers
    for i in range(1, 16):  # 15 subscribers
        subscriber = Subscriber(
            msisdn=f"155512{i:05d}", 
            imsi=f"31026000000{i:05d}"
        )
        subscriber.apn = us_carrier.apns[0] if i % 3 != 0 else us_carrier.apns[1]
        us_carrier.add_subscriber(subscriber)
    
    # Asian Carrier (roaming partners)
    asia_carrier = Carrier(name="AsiaTel", mcc_mnc="45005", country_code="82")
    asia_carrier.add_apn(APN(apn="internet.kt", ip_pool_cidr="203.248.0.0/16"))
    
    # Add Asian subscribers
    for i in range(1, 11):  # 10 subscribers
        subscriber = Subscriber(
            msisdn=f"821012345{i:03d}", 
            imsi=f"45005000000{i:05d}"
        )
        subscriber.apn = asia_carrier.apns[0]
        asia_carrier.add_subscriber(subscriber)
    
    return [eu_carrier, us_carrier, asia_carrier]


def main():
    print("🌍 Starting Advanced Multi-Service Network Example")
    
    # Create telecom network
    network = TelecomNetwork("GlobalTelecom")
    
    # Setup infrastructure
    network.setup_infrastructure()
    
    # Add carriers
    carriers = create_test_carriers()
    for carrier in carriers:
        network.add_carrier(carrier)
        print(f"   📋 Added {carrier.name}: {len(carrier.subscribers)} subscribers")
    
    print(f"\n🎯 Network Ready:")
    print(f"   🏢 Carriers: {len(network.carriers)}")
    print(f"   👥 Total Subscribers: {sum(len(c.subscribers) for c in network.carriers)}")
    print(f"   🔧 Services: {list(network.services.keys())}")
    
    # Run activity simulation
    try:
        network.simulate_subscriber_activity(duration_seconds=30)
    except KeyboardInterrupt:
        print("\n⏹️ Simulation interrupted by user")
    finally:
        # Cleanup
        network.shutdown()
        print("✅ Advanced Multi-Service example completed!")


if __name__ == "__main__":
    main()
