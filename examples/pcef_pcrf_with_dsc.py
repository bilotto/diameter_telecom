import logging
logging.basicConfig(level=logging.DEBUG)

from diameter_telecom import *
from diameter_telecom.services.service import Service

pcrf = PCRF(origin_host="pcrf", realm_name="realm", ip_addresses=["127.0.0.1"], tcp_port=3868, vendor_ids=[10415,])
pcef = PCEF(origin_host="pcef", realm_name="realm", ip_addresses=["127.0.0.1"], tcp_port=3869, vendor_ids=[10415,])

dsc = DSC(origin_host="dsc", realm_name="realm", ip_addresses=["127.0.0.1"], tcp_port=3870, vendor_ids=[10415,])

pcrf.add_node_as_peer(dsc.node, app_id=APP_3GPP_GX, initiate_connection=False)
pcef.add_node_as_peer(dsc.node, app_id=APP_3GPP_GX, initiate_connection=False)

dsc.add_node_as_peer(pcrf.node, app_id=APP_3GPP_GX, initiate_connection=True)
dsc.add_node_as_peer(pcef.node, app_id=APP_3GPP_GX, initiate_connection=True)

pcrf.setup_apps()
pcef.setup_apps()
dsc.setup_apps()

pcrf.start()
pcef.start()
dsc.start()

pcrf.wait_for_ready()
pcef.wait_for_ready()
dsc.wait_for_ready()

carrier = Carrier(name="ZetaTel", mcc_mnc="72488", country_code="55")
subscriber = Subscriber(msisdn="5511999999999", imsi="724880000000000")
carrier.add_subscriber(subscriber)

ip_queue = IpQueue("10.10.0.0/16")

# data_service = DataService(pcef=pcef, ip_queue=ip_queue)
service = Service(pcef=pcef, ip_queue=ip_queue)

gx_session = service.create_gx_session(subscriber)
gx_session.rat_type = E_RAT_TYPE_EUTRAN

service.start_gx_session(gx_session)


import sys

import pprint

def pretty_display(value):
    if value is not None:
        pprint.pprint(value)

sys.displayhook = pretty_display


service.session_manager

# pcrf.stop()
# pcef.stop()
# dsc.stop()