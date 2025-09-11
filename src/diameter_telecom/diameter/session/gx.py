from ._diameter_session import *
from ..parse_avp import *
from typing import *

@dataclass
class GxSession(DiameterSession):
    framed_ip_address: Optional[str] = field(default=None)
    framed_ipv6_prefix: Optional[str] = field(default=None)
    called_station_id: Optional[str] = field(default=None)
    sgsn_mcc_mnc: Optional[str] = field(default=None)
    granted_service_unit: Optional[Dict] = field(default_factory=dict)
    event_trigger: Optional[List[int]] = field(default_factory=list)
    cc_request_number: Optional[int] = field(default=None)

    @property
    def apn(self):
        return self.called_station_id

    def add_message(self, message: DiameterMessage):
        """Add message to session - business logic now handled by SessionManager"""
        return super().add_message(message)
