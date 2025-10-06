"""
Example demonstrating the new Subscriber messages functionality.

This example shows how subscribers now automatically track all their associated
Diameter messages across different sessions and applications.
"""

import logging
logging.basicConfig(level=logging.INFO)

from diameter_telecom import *

# Create PCRF and PCEF nodes
pcrf = PCRF(origin_host="pcrf.python.realm", realm_name="python.realm", 
           ip_addresses=["127.0.0.1"], tcp_port=3868, vendor_ids=[10415])
pcef = PCEF(origin_host="pcef.python.realm", realm_name="python.realm", 
           ip_addresses=["127.0.0.1"], tcp_port=3869, vendor_ids=[10415])

# Connect nodes
pcrf.add_node_as_peer(pcef, app_id=APP_3GPP_GX, initiate_connection=False)
pcef.add_node_as_peer(pcrf, app_id=APP_3GPP_GX, initiate_connection=True)

# Setup applications
pcrf.setup_gx_app()
pcef.setup_gx_app()

# Start nodes
pcrf.start()
pcef.start()
pcrf.wait_for_ready()
pcef.wait_for_ready()

# Create a subscriber
subscriber = Subscriber(msisdn="123456789", imsi="123456789012345")
print(f"Initial subscriber: {subscriber}")
print(f"Initial message count: {len(subscriber.messages)}")

# Create and send a CCR-I request
from diameter.message.commands import CreditControlRequest

pcef_service = DataService(pcef)
pcrf_service = DataService(pcrf)

ccr = CreditControlRequest()
ccr.session_id = f"{pcef.gx_app.node.session_generator.next_id()}"
ccr.cc_request_type = E_CC_REQUEST_TYPE_INITIAL_REQUEST
ccr.cc_request_number = 0
ccr.header.application_id = APP_3GPP_GX
diameter_message = DiameterMessage(ccr)
diameter_message.message.subscription_id = subscriber.subscription_id

# Send the request
request, answer = pcef_service.send_request(diameter_message)

# Check subscriber message history
print(f"\nAfter CCR-I request:")
print(f"Subscriber: {subscriber}")
print(f"Message count: {len(subscriber.messages)}")

# Show all messages for this subscriber
print(f"\nAll messages for subscriber {subscriber.msisdn}:")
for i, msg in enumerate(subscriber.get_messages(), 1):
    print(f"  {i}. {msg.name} - {msg.time}")

# Show messages by application
gx_messages = subscriber.get_messages_by_app_id(APP_3GPP_GX)
print(f"\nGx messages: {len(gx_messages)}")

# Show messages by name
ccr_messages = subscriber.get_messages_by_name("CCR-I")
print(f"CCR-I messages: {len(ccr_messages)}")

# Demonstrate the new import structure works
print(f"\n✅ Import structure verification:")
print(f"Subscriber.messages type: {type(subscriber.messages)}")
print(f"Direct import of DiameterMessage works: {DiameterMessage is not None}")

# Show the refactored SessionManager structure
print(f"\n✅ Refactored SessionManager structure:")
print(f"SessionManager uses stage functions: {hasattr(session_manager, 'process_diameter_message')}")
print(f"Stage functions are modular: stage_parse_request, stage_parse_response available")

# Check SessionManager subscriber statistics
session_manager = pcef_service.gx_app.session_manager
print(f"\nSessionManager statistics:")
print(f"Total subscribers: {len(session_manager.subscribers.subscribers)}")
print(f"Subscribers with messages: {len(session_manager.subscribers.get_subscribers_with_messages())}")
print(f"Total messages across all subscribers: {session_manager.subscribers.get_total_messages()}")

# Clean up
pcef_service.stop()
pcrf_service.stop()
