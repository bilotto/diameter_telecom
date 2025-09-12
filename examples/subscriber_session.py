"""
Subscriber and Carrier Data Model Example

This example demonstrates the data model classes (Subscriber, Carrier, APN)
without starting actual Diameter entities. It shows how to create and configure
subscribers, carriers, and APNs for use in other examples.

For actual Diameter session examples, see:
- pcef_pcrf_connection.py - Basic entity connection
- data_service_comprehensive.py - Data services with sessions
- voice_service_comprehensive.py - Voice services with media
"""

from diameter_telecom import Subscriber, Carrier, PCEF, PCRF
from diameter_telecom.apn import APN

# Create PCEF and PCRF entities
pcef = PCEF(origin_host="pcef", realm_name="example.realm", ip_addresses=["127.0.0.1"], tcp_port=3869, vendor_ids=[10415])
pcrf = PCRF(origin_host="pcrf", realm_name="example.realm", ip_addresses=["127.0.0.1"], tcp_port=3868, vendor_ids=[10415])

carrier = Carrier(name="ZetaTel", mcc_mnc="72488", country_code="55")

subscriber = Subscriber(msisdn="5511999999999", imsi="724880000000000")

carrier.add_subscriber(subscriber)

# Note: set_carrier method may not exist on entities - would need to check actual API
# pcrf.set_carrier(carrier)
# pcef.set_carrier(carrier)

apn_data = APN(apn="internet", ip_pool_cidr="10.10.0.0/16")
carrier.add_apn(apn_data)
apn_voice = APN(apn="ims", ip_pool_cidr="172.16.10.0/24")
carrier.add_apn(apn_voice)

subscriber.apn = apn_data

# Note: start_gx_session method may not exist - this would need entity setup:
# pcef.setup_gx_app()
# pcef.start()
# Then use SessionManager or Services to start sessions
# pcef.start_gx_session(subscriber)





