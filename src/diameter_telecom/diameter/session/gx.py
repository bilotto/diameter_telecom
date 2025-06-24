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
        diameter_message = super().add_message(message)
        if not diameter_message:
            return
        if diameter_message.is_request:
            if diameter_message.name == CCR_I:
                if diameter_message.timestamp:
                    self.start_time = diameter_message.timestamp
                if diameter_message.message.framed_ip_address:
                    if not self.framed_ip_address:
                        self.framed_ip_address = diameter_message.message.framed_ip_address
                if diameter_message.message.framed_ipv6_prefix:
                    if not self.framed_ipv6_prefix:
                        self.framed_ipv6_prefix = diameter_message.message.framed_ipv6_prefix
                if diameter_message.message.called_station_id:
                    if not self.called_station_id:
                        self.called_station_id = diameter_message.message.called_station_id
                if diameter_message.message.sgsn_mcc_mnc:
                    if not self.sgsn_mcc_mnc:
                        self.sgsn_mcc_mnc = diameter_message.message.sgsn_mcc_mnc
                if diameter_message.message.subscription_id:
                    if not self.subscriber:
                        msisdn, imsi, sip_uri, nai, private = parse_subscription_id(diameter_message.message.subscription_id)
                        self.subscriber = Subscriber(msisdn=msisdn, imsi=imsi)
        else:
            if diameter_message.result_code and diameter_message.result_code != E_RESULT_CODE_DIAMETER_SUCCESS:
                self.error = True
            if diameter_message.name == CCA_I:
                if diameter_message.timestamp and diameter_message.result_code == E_RESULT_CODE_DIAMETER_SUCCESS:
                    self.active = True
            elif diameter_message.name == CCA_T:
                if diameter_message.timestamp:
                    self.active = False
                    self.ended = True
                    self.end_time = diameter_message.timestamp
        #
        if not diameter_message.subscriber and self.subscriber:
            diameter_message.subscriber = self.subscriber
