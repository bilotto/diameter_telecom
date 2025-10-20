from dataclasses import dataclass, field
from typing import Optional, Dict

from ._diameter_session import DiameterSession
from ..constants import *

from ..apn import ip_to_bytes, bytes_to_ip


@dataclass
class RxSession(DiameterSession):
    app_id: int = APP_3GPP_RX
    # Not an AVP, but used to link the Rx session to the Gx session
    gx_session_id: Optional[str] = field(default=None)
    _avps: Dict[str, str] = field(default_factory=dict, repr=False)
    
    @property
    def avps(self) -> Dict[str, str]:
        avps = dict()
        for key, value in self._avps.items():
            if key == 'framed_ip_address':
                value = ip_to_bytes(value)
            avps[key] = value
        avps['session_id'] = self.session_id
        return avps


    def set_gx_session_id(self, gx_session_id: str):
        self.gx_session_id = gx_session_id

    def add_message(self, message):
        """Add message to session - business logic now handled by SessionManager"""
        return super().add_message(message)

    def to_dict(self) -> dict:
        session_data = super().to_dict()
        if self.gx_session_id:
            session_data['gx_session_id'] = self.gx_session_id
        return session_data