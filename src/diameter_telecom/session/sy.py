from dataclasses import dataclass, field
from typing import Optional, List

from ._diameter_session import DiameterSession
from ..constants import *

from ..message import DiameterMessage
from diameter.message.avp.grouped import PolicyCounterStatusReport
from ..diameter_layer.parse_avp import parse_policy_counter_status_report

@dataclass
class SySession(DiameterSession):
    app_id: int = APP_3GPP_SY
    gx_session_id: Optional[str] = field(default=None)
    policy_counter_status_report: Optional[List[PolicyCounterStatusReport]] = field(default_factory=list)

    def set_gx_session_id(self, gx_session_id: str):
        self.gx_session_id = gx_session_id

    def add_message(self, diameter_message: DiameterMessage):
        message = diameter_message.message
        if hasattr(message, 'policy_counter_status_report'):
            self.logger.debug(f"Adding policy_counter_status_report to session: {message.policy_counter_status_report}")
            policy_counter_status_report_dict = parse_policy_counter_status_report(message.policy_counter_status_report)
            self.policy_counter_status_report = policy_counter_status_report_dict
            self.logger.debug(f"Policy counter status report: {self.policy_counter_status_report}")
        return super().add_message(diameter_message)

    def to_dict(self) -> dict:
        session_data = super().to_dict()
        if self.gx_session_id:
            session_data['gx_session_id'] = self.gx_session_id
        return session_data