from dataclasses import dataclass, field
from typing import Optional, Dict

from ._diameter_session import DiameterSession
from ..constants import *


@dataclass
class RxSession(DiameterSession):
    app_id: int = APP_3GPP_RX
    gx_session_id: Optional[str] = field(default=None)
    _avps: Dict[str, str] = field(default_factory=dict, repr=False)
    
    @property
    def avps(self) -> Dict[str, str]:
        self._avps = {}
        for key, value in self.subscriber.avps.items():
            self._avps[key] = value
        return self._avps

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