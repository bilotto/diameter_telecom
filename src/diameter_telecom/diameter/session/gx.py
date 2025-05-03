from ._diameter_session import *

@dataclass
class GxSession(DiameterSession):
    framed_ip_address: Optional[str] = field(default=None)
    framed_ipv6_prefix: Optional[str] = field(default=None)
    apn: Optional[str] = field(default=None)
    mcc_mnc: Optional[str] = field(default=None)

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
                self.apn = message.called_station_id
                
        elif message.name == CCR_T:
            if message.timestamp:
                self.end(message.timestamp)
            else:
                self.end()
