from pcef import pcef
from pcrf import pcrf
from diameter_telecom import Subscriber, Carrier
from diameter_telecom.apn import APN

carrier = Carrier(name="ZetaTel", mcc_mnc="72488", country_code="55")

subscriber = Subscriber(msisdn="5511999999999", imsi="724880000000000")

carrier.add_subscriber(subscriber)

pcrf.set_carrier(carrier)
pcef.set_carrier(carrier)

apn_data = APN(apn="internet", ip_pool_cidr="10.10.0.0/16")
carrier.add_apn(apn_data)
apn_voice = APN(apn="ims", ip_pool_cidr="172.16.10.0/24")
carrier.add_apn(apn_voice)

subscriber.apn = apn_data

pcef.start_gx_session(subscriber)





