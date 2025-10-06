from ._diameter_session import *
from ..parse_avp import *
from typing import *
from diameter.message.commands import CreditControlRequest, CreditControlAnswer
from ..message import DiameterMessage

@dataclass
class GxSession(DiameterSession):
    framed_ip_address: Optional[str] = field(default=None)
    framed_ipv6_prefix: Optional[str] = field(default=None)
    called_station_id: Optional[str] = field(default=None)
    sgsn_mcc_mnc: Optional[str] = field(default=None)
    granted_service_unit: Optional[Dict] = field(default_factory=dict)
    event_trigger: Optional[List[int]] = field(default_factory=list)
    cc_request_number: Optional[int] = field(default=None)
    rat_type: Optional[int] = field(default=None)
    _avps: Dict[str, str] = field(default_factory=dict, repr=False)

    @property
    def avps(self) -> Dict[str, str]:
        if self.framed_ip_address:
            self._avps['framed_ip_address'] = self.framed_ip_address
        if self.framed_ipv6_prefix:
            self._avps['framed_ipv6_prefix'] = self.framed_ipv6_prefix
        if self.called_station_id:
            self._avps['called_station_id'] = self.called_station_id
        if self.sgsn_mcc_mnc:
            self._avps['sgsn_mcc_mnc'] = self.sgsn_mcc_mnc
        if self.rat_type:
            self._avps['rat_type'] = self.rat_type
        # if self.cc_request_number:
        #     self._avps['cc_request_number'] = self.cc_request_number
        for key, value in self.subscriber.avps.items():
            self._avps[key] = value
        return self._avps

    @property
    def apn(self):
        return self.called_station_id

    def add_message(self, diameter_message: DiameterMessage):
        message = diameter_message.message
        """Add message to session - business logic now handled by SessionManager"""
        if isinstance(message, CreditControlRequest):
            self.cc_request_number = message.cc_request_number
        elif isinstance(message, CreditControlAnswer):
            self.cc_request_number = message.cc_request_number
        else:
            pass
        if hasattr(message, 'rat_type'):
            if not self.rat_type:
                self.rat_type = message.rat_type
            else:
                if self.rat_type != message.rat_type:
                    logger.warning(f"🚨 GxSession: Rat type changed from {self.rat_type} to {message.rat_type}")
                    self.rat_type = message.rat_type
        return super().add_message(message)

    def to_json(self) -> dict:
        """
        Convert GxSession to JSON-serializable dictionary.
        """
        session_data = super().to_json()
        if self.framed_ip_address:
            session_data['framed_ip_address'] = self.framed_ip_address
        if self.framed_ipv6_prefix:
            session_data['framed_ipv6_prefix'] = self.framed_ipv6_prefix
        if self.called_station_id:
            session_data['called_station_id'] = self.called_station_id

        return session_data