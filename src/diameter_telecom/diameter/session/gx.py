from ._diameter_session import *
from ..parse_avp import *

@dataclass
class GxSession(DiameterSession):
    framed_ip_address: Optional[str] = field(default=None)
    framed_ipv6_prefix: Optional[str] = field(default=None)
    called_station_id: Optional[str] = field(default=None)
    sgsn_mcc_mnc: Optional[str] = field(default=None)

    @property
    def apn(self):
        return self.called_station_id

    def add_message(self, message: DiameterMessage):
        super().add_message(message)
        if message.name == CCR_I:
            if message.timestamp:
                self.start(message.timestamp)
            else:
                self.start()
            if message.framed_ip_address:
                self.framed_ip_address = message.framed_ip_address
            if message.framed_ipv6_prefix:
                self.framed_ipv6_prefix = message.framed_ipv6_prefix
            if message.called_station_id:
                self.called_station_id = message.called_station_id
            if message.sgsn_mcc_mnc:
                self.sgsn_mcc_mnc = message.sgsn_mcc_mnc
            if message.subscription_id:
                msisdn, imsi, sip_uri, nai, private = parse_subscription_id(message.subscription_id)
                if not self.subscriber:
                    self.subscriber = Subscriber(msisdn=msisdn, imsi=imsi)
        elif message.name == CCR_T:
            if message.timestamp:
                self.end(message.timestamp)
            else:
                self.end()
        if not message.subscriber:
            message.subscriber = self.subscriber
