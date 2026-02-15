from dataclasses import dataclass, field
from typing import Dict, Optional, Any
import logging
from ..message import DiameterMessage
from ..session._diameter_session import DiameterSession
from ..subscriber import Subscriber

from ..diameter_layer.parse_avp import *

logger = logging.getLogger("diameter_telecom.session_manager")


@dataclass
class MessageProcessingContext:
    """
    Processing context for Diameter message pipeline.
    
    Contains all data accumulated during message processing including
    the original message, extracted identifiers, resolved session,
    subscriber, and additional processing data.
    
    This class replaces the previous gv_stages dict pattern with a
    strongly-typed, extensible context object.
    """
    # Core message data (always present)
    message: DiameterMessage
    session_id: str
    app_id: int
    message_flow_type: Optional[str] = None  # START, UPDATE, REFRESH, TERMINATE, UNKNOWN
    owner_app: Optional[Any] = None  # Reference to the application object that processed this message
    owner_key: Optional[str] = None  # Stable registry key of the owner in SessionManager
    framed_ip_address: Optional[str] = None
    framed_ipv6_prefix: Optional[str] = None
    called_station_id: Optional[str] = None
    sgsn_mcc_mnc: Optional[str] = None
    # Processing results (populated by pipeline)
    session: Optional[DiameterSession] = None
    subscriber: Optional[Subscriber] = None
    msisdn: Optional[str] = None
    imsi: Optional[str] = None
    result_code: Optional[int] = None
    session_active: bool = False
    origin_host: Optional[str] = None
    origin_realm: Optional[str] = None
    destination_host: Optional[str] = None
    destination_realm: Optional[str] = None
    is_request: bool = False
    
    # Pipeline stage results
    validated: bool = False
    validation_errors: Optional[list] = None
    should_stop: bool = False
    session_found: bool = False
    subscriber_found: bool = False
    subscriber_created: bool = False
    subscriber_resolution_method: Optional[str] = None
    session_created: bool = False
    session_started: bool = False
    session_bound: bool = False
    binding_method: Optional[str] = None
    session_refreshed: bool = False
    session_terminated: bool = False
    session_updated: bool = False
    error_handled: bool = False
    message_stored: bool = False
    session_id_added: bool = False
    
    # Pipeline configuration (set by main pipeline)
    sessions: Optional[Any] = None  # Sessions collection
    subscribers: Optional[Any] = None  # Subscribers collection
    clear_sessions_after_termination: bool = False
    save_messages_to_session: bool = True
    save_messages_to_subscriber: bool = True
    save_session_ids_to_subscriber: bool = True
    enable_session_binding: bool = True
    
    # Extensible data storage for pipeline stages
    _additional_data: Dict[str, Any] = field(default_factory=dict)
    stop_processing: bool = False

    # Pcap support
    pcap_filepath: Optional[str] = None
    frame_number: Optional[int] = None

    # @property
    # def session_id(self):
    #     return self.message.session_id

    # @property
    # def app_id(self):
    #     return self.message.app_id


    def __getitem__(self, key: str) -> Any:
        """Dict-like access for backward compatibility with existing pipeline code."""
        # Check core attributes first
        if key == 'dm':
            return self.message
        elif hasattr(self, key):
            return getattr(self, key)
        # Fall back to additional data
        else:
            return self._additional_data[key]
    
    def __setitem__(self, key: str, value: Any):
        """Dict-like assignment for backward compatibility with existing pipeline code."""
        # Handle core attributes
        if key == 'dm':
            self.message = value
        elif hasattr(self, key):
            setattr(self, key, value)
        # Store in additional data
        else:
            self._additional_data[key] = value
    
    def get(self, key: str, default=None) -> Any:
        """Dict-like get method for backward compatibility."""
        try:
            return self[key]
        except (KeyError, AttributeError):
            return default
    
    def __contains__(self, key: str) -> bool:
        """Dict-like 'in' operator support."""
        if key == 'dm':
            return True
        elif hasattr(self, key):
            return True
        else:
            return key in self._additional_data
    
    def keys(self):
        """Dict-like keys() method for iteration."""
        core_keys = ['dm', 'message', 'session_id', 'app_id', 'owner_key', 'session', 'subscriber']
        return core_keys + list(self._additional_data.keys())

    def _resolve_return_value(self, value: Any) -> str:
        if isinstance(value, list) or isinstance(value, set):
            return "|".join(str(item) for item in value)
        elif isinstance(value, dict):
            return "|".join(f"{k}:{v}" for k, v in value.items())
        elif isinstance(value, bytes):
            return value.decode()
        else:
            return str(value).strip()
    
    def resolve_attribute(self, attr_name: str) -> str:
        try:
            if attr_name in self._additional_data:
                value = self._additional_data[attr_name]
                if value is not None:
                    return self._resolve_return_value(value)

            if self.session and hasattr(self.session, attr_name):
                value = getattr(self.session, attr_name)
                if value is not None:
                    return self._resolve_return_value(value)

            if hasattr(self.message, attr_name):
                value = getattr(self.message, attr_name)
                if value is not None:
                    return self._resolve_return_value(value)
                        
            if self.subscriber and hasattr(self.subscriber, attr_name):
                value = getattr(self.subscriber, attr_name)
                if value is not None:
                    return self._resolve_return_value(value)
            
            if hasattr(self, attr_name):
                value = getattr(self, attr_name)
                if value is not None:
                    return self._resolve_return_value(value)

            return ""
            
        except Exception as e:
            logger.warning(f"Error resolving attribute '{attr_name}': {e}")
            return ""
    
    @classmethod
    def from_diameter_message(cls, dm: DiameterMessage) -> 'MessageProcessingContext':
        """
        Factory method to create MessageProcessingContext from DiameterMessage.
        
        Args:
            dm: The DiameterMessage to process
            
        Returns:
            MessageProcessingContext: New context initialized with the message
        """
        context = cls(message=dm, session_id=dm.session_id, app_id=dm.app_id)
        context.is_request = dm.is_request
        if hasattr(dm.message, 'framed_ip_address') and dm.message.framed_ip_address:
            framed_ip_address = decode_framed_ip_address(dm.message.framed_ip_address)
            context.framed_ip_address = framed_ip_address
        if hasattr(dm.message, 'framed_ipv6_prefix') and dm.message.framed_ipv6_prefix:
            framed_ipv6_prefix = dm.message.framed_ipv6_prefix
            context.framed_ipv6_prefix = framed_ipv6_prefix
        if hasattr(dm.message, 'called_station_id') and dm.message.called_station_id:
            called_station_id = dm.message.called_station_id
            context.called_station_id = called_station_id
        if hasattr(dm.message, 'sgsn_mcc_mnc') and dm.message.sgsn_mcc_mnc:
            sgsn_mcc_mnc = dm.message.sgsn_mcc_mnc
            context.sgsn_mcc_mnc = sgsn_mcc_mnc
        if hasattr(dm.message, 'subscription_id') and dm.message.subscription_id:
            msisdn, imsi, sip_uri, nai, private_id = parse_subscription_id(dm.message.subscription_id)
            if msisdn:
                context.msisdn = msisdn
            if imsi:
                context.imsi = imsi
        # Extract result code, checking both Result-Code and Experimental-Result-Code
        if hasattr(dm.message, 'result_code') and dm.message.result_code:
            context.result_code = dm.message.result_code
        elif hasattr(dm.message, 'experimental_result_code') and dm.message.experimental_result_code:
            # Fallback to Experimental-Result-Code if Result-Code is not present
            context.result_code = dm.message.experimental_result_code
        elif hasattr(dm.message, 'experimental_result') and dm.message.experimental_result:
            # Experimental-Result is a grouped AVP, extract Experimental-Result-Code from it
            if hasattr(dm.message.experimental_result, 'experimental_result_code'):
                context.result_code = dm.message.experimental_result.experimental_result_code
        if hasattr(dm.message, 'origin_host') and dm.message.origin_host:
            context.origin_host = dm.message.origin_host.decode()
        # if hasattr(dm.message, 'origin_realm') and dm.message.origin_realm:
        #     context.origin_realm = dm.message.origin_realm
        # if hasattr(dm.message, 'destination_host') and dm.message.destination_host:
        #     context.destination_host = dm.message.destination_host
        # if hasattr(dm.message, 'destination_realm') and dm.message.destination_realm:
        #     context.destination_realm = dm.message.destination_realm
        if hasattr(dm.message, 'policy_counter_status_report') and dm.message.policy_counter_status_report:
            context._additional_data['policy_counter_status_report'] = parse_policy_counter_status_report(dm.message.policy_counter_status_report)
        if hasattr(dm.message, 'charging_rule_install') and dm.message.charging_rule_install:
            context._additional_data['charging_rule_install'] = check_charging_rule_install(dm)
        if hasattr(dm.message, 'charging_rule_remove') and dm.message.charging_rule_remove:
            context._additional_data['charging_rule_remove'] = check_charging_rule_remove(dm)
        if hasattr(dm.message, 'cc_request_number') and dm.message.cc_request_number:
            context._additional_data['cc_request_number'] = dm.message.cc_request_number

        return context
    