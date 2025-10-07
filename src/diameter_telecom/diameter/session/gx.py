from ._diameter_session import *
from ..parse_avp import *
from typing import *
from diameter.message.commands import CreditControlRequest, CreditControlAnswer
from ..message import DiameterMessage
from diameter.message.avp.grouped import ChargingRuleInstall

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
    charging_rule_base_name: Optional[List[Any]] = field(default_factory=list)
    charging_rule_name: Optional[List[Any]] = field(default_factory=list)

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
        if isinstance(diameter_message, Message):
            logger.warning(f"🚨 GxSession: Message is not a DiameterMessage")
            message = diameter_message
        else:
            message = diameter_message.message

        # Add active event triggers to session
        if diameter_message.name in [CCA_I, CCA_U, RAR]:
            if message.event_trigger:
                for event_trigger in message.event_trigger:
                    if event_trigger not in self.event_trigger:
                        self.event_trigger.append(event_trigger)
            if message.charging_rule_install:
                for charging_rule_install in message.charging_rule_install:
                    if not isinstance(charging_rule_install, ChargingRuleInstall):
                        raise ValueError(f"Charging rule install is not a ChargingRuleInstall")
                    if charging_rule_install.charging_rule_base_name:
                        self.charging_rule_base_name.append(charging_rule_install.charging_rule_base_name)
                    if charging_rule_install.charging_rule_name:
                        self.charging_rule_name.append(charging_rule_install.charging_rule_name)

        # Make sure cc_request_number is updated
        if isinstance(message, CreditControlRequest):
            self.cc_request_number = message.cc_request_number
        elif isinstance(message, CreditControlAnswer):
            self.cc_request_number = message.cc_request_number
        else:
            pass
        
        # Update rat type
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
        if self.charging_rule_base_name:
            session_data['charging_rule_base_name'] = self.charging_rule_base_name
        if self.charging_rule_name:
            session_data['charging_rule_name'] = self.charging_rule_name
        return session_data