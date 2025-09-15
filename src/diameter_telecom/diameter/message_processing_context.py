from dataclasses import dataclass, field
from typing import Dict, Optional, Any
import logging
from .message import DiameterMessage
from .session import DiameterSession
from ..subscriber import Subscriber

from .parse_avp import *

logger = logging.getLogger(__name__)


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
    
    # Extensible data storage for pipeline stages
    _additional_data: Dict[str, Any] = field(default_factory=dict)
    stop_processing: bool = False

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
        core_keys = ['dm', 'message', 'session_id', 'app_id', 'session', 'subscriber']
        return core_keys + list(self._additional_data.keys())
    
    def resolve_attribute(self, attr_name: str) -> str:
        """
        Smart attribute resolution for CSV generation and other use cases.
        
        Resolution priority:
        1. DiameterMessage attributes (direct properties and __getattr__)
        2. Session attributes (if session exists)
        3. Subscriber attributes (if subscriber exists)
        4. Additional data from pipeline stages
        5. Default empty string
        
        Args:
            attr_name: Name of the attribute to resolve
            
        Returns:
            str: String representation of the attribute value, or empty string if not found
        """
        try:

            if self.session and hasattr(self.session, attr_name):
                value = getattr(self.session, attr_name)
                if value is not None:
                    return str(value).strip()

            # 1. Try DiameterMessage first (includes properties like msisdn, imsi via subscriber)
            if hasattr(self.message, attr_name):
                value = getattr(self.message, attr_name)
                if value is not None:
                    return str(value).strip()
            
            # # Handle special case for 'dm' key (backward compatibility)
            # if attr_name == 'dm':
            #     return str(self.message).strip() if self.message else ""
            
            # 2. Try Session attributes (e.g., GxSession.apn, framed_ip_address, sgsn_mcc_mnc)

            
            # 3. Try Subscriber attributes (direct access)
            if self.subscriber and hasattr(self.subscriber, attr_name):
                value = getattr(self.subscriber, attr_name)
                if value is not None:
                    return str(value).strip()
            
            # 4. Try additional pipeline data
            if attr_name in self._additional_data:
                value = self._additional_data[attr_name]
                if value is not None:
                    return str(value).strip()
            
            # 5. Try core context attributes
            if hasattr(self, attr_name):
                value = getattr(self, attr_name)
                if value is not None:
                    return str(value).strip()


            
            # 6. Default to empty string
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
        if hasattr(dm.message, 'result_code') and dm.message.result_code:
            context.result_code = dm.message.result_code

        return context
    
    # def to_dict(self) -> Dict[str, Any]:
    #     """
    #     Convert context to dictionary for logging/debugging purposes.
        
    #     Returns:
    #         Dict containing all context data
    #     """
    #     result = {
    #         'session_id': self.session_id,
    #         'app_id': self.app_id,
    #         'message_name': self.message.name if self.message else None,
    #         'has_session': self.session is not None,
    #         'has_subscriber': self.subscriber is not None,
    #         'additional_data_keys': list(self._additional_data.keys())
    #     }
        
    #     if self.session:
    #         result['session_type'] = type(self.session).__name__
    #         result['session_active'] = getattr(self.session, 'active', None)
        
    #     if self.subscriber:
    #         result['subscriber_msisdn'] = self.subscriber.msisdn
    #         result['subscriber_imsi'] = getattr(self.subscriber, 'imsi', None)
        
    #     return result
    
    # def __repr__(self) -> str:
    #     """String representation for debugging."""
    #     return (f"MessageProcessingContext("
    #             f"message={self.message.name if self.message else None}, "
    #             f"session_id={self.session_id}, "
    #             f"app_id={self.app_id}, "
    #             f"has_session={self.session is not None}, "
    #             f"has_subscriber={self.subscriber is not None}"
    #             f")")
