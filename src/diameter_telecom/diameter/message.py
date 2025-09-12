from diameter.message.commands import *
from diameter.message.avp.grouped import *
from diameter.message import Message, dump
from .constants import *
from typing import TYPE_CHECKING
import datetime
import logging

if TYPE_CHECKING:
    from ..subscriber import Subscriber
logger = logging.getLogger(__name__)

def convert_timestamp(timestamp: str) -> str:
    return datetime.datetime.fromtimestamp(float(timestamp), tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

class DiameterMessage:
    message: CreditControlRequest | ReAuthRequest | AbortSessionRequest | SpendingLimitRequest | SpendingStatusNotificationRequest | SessionTerminationRequest | AaRequest | CreditControlAnswer | ReAuthAnswer | AbortSessionAnswer | SpendingLimitAnswer | SpendingStatusNotificationAnswer | SessionTerminationAnswer | AaAnswer | DisconnectPeerRequest | DisconnectPeerAnswer
    def __init__(self, obj):
        if isinstance(obj, Message):
            self.message = obj
        elif isinstance(obj, str):
            try:
                hex_string = obj.strip().replace(':', '')
                message_bytes = bytes.fromhex(hex_string)
                self.message = Message.from_bytes(message_bytes)
            except ValueError:
                raise ValueError("Invalid hex string provided.")
        else:
            raise TypeError(f"Parameter must be a hex string or a Message instance. Provided: {obj},{type(obj)}")
        
        self.timestamp = None
        self.subscriber: 'Subscriber' = None

    def __getattr__(self, name):
        if hasattr(self.message, name):
            return getattr(self.message, name)
        return None

    @property
    def name(self):
        return name_diameter_message(self)
    
    @property
    def message_name(self):
        return self.name
    
    @property
    def app_id(self):
        return self.message.header.application_id
    
    @property
    def is_request(self):
        return self.message.header.is_request

    @property
    def hex_string(self):
        return self.message.as_bytes().hex()
    
    @property
    def msisdn(self):
        return self.subscriber.msisdn if self.subscriber else None
    
    @property
    def imsi(self):
        return self.subscriber.imsi if self.subscriber else None
    
    @property
    def time(self):
        if self.timestamp:
            return datetime.datetime.fromtimestamp(float(self.timestamp), tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return None
    
    @property
    def hop_by_hop_id(self):
        return self.message.header.hop_by_hop_identifier
    
    @property
    def end_to_end_id(self):
        return self.message.header.end_to_end_identifier
    
    def dump_hex_string(self, file_full_path):
        with open(file_full_path, 'w') as f:
            f.write(self.hex_string)
        logger.info(f"Hex string written to {file_full_path}")

    def dump(self):
        return dump(self.message)
    
    def __repr__(self):
        if self.subscriber:
            return f"{self.time},{self.name},{self.subscriber.msisdn}"
        else:
            return f"{self.time},{self.name}"
    
    def __eq__(self, other):
        return self.hop_by_hop_id == other.hop_by_hop_id and self.end_to_end_id == other.end_to_end_id and self.is_request == other.is_request
    
    def __hash__(self):
        return hash((self.hop_by_hop_id, self.end_to_end_id, self.is_request))
    
    def set_message_attribute(self, name, value):
        if not hasattr(self.message, name):
            raise ValueError(f"Attribute {name} not found in message")
        setattr(self.message, name, value)

    @property
    def session_id(self):
        if hasattr(self.message, 'session_id'):
            return self.message.session_id

    def to_json(self) -> dict:
        """
        Convert DiameterMessage to JSON-serializable dictionary.
        
        Returns:
            dict: JSON-serializable representation of the message
        """
        try:
            message_data = dict()
            message_data['is_request'] = self.is_request
            message_data['name'] = self.name
            message_data['time'] = self.time
            if hasattr(self.message, 'result_code') and self.message.result_code is not None:
                message_data['result_code'] = self.message.result_code
            
            # Convert any bytes objects to appropriate string format
            for key, value in message_data.items():
                if isinstance(value, bytes):
                    try:
                        message_data[key] = value.decode('utf-8')
                    except UnicodeDecodeError:
                        message_data[key] = value.hex()
                elif value is not None and not isinstance(value, (str, int, float, bool, list, dict)):
                    message_data[key] = str(value)
            
            return message_data
            
        except Exception as e:
            logger.exception(f"Failed to serialize DiameterMessage")
            return {
                "session_id": getattr(self, 'session_id', None),
                "name": getattr(self, 'name', None),
                "error": f"Serialization failed: {str(e)}"
            }


def name_diameter_message(diameter_message: DiameterMessage) -> str | None:
    """
    Get the name of a diameter message based on its type and request/response status.
    
    This function determines the appropriate name for a Diameter message based on
    its type (e.g., Credit Control, Re-Auth, etc.) and whether it's a request or
    answer message.
    
    Args:
        diameter_message: The DiameterMessage instance to name
        
    Returns:
        str: The message name (e.g., CCR-I, CCA-I, RAR, RAA, etc.) or None if not recognized
    """
    message = diameter_message.message
    is_request = message.header.is_request

    if isinstance(message, CreditControl):
        cc_type_mapping = {
            E_CC_REQUEST_TYPE_INITIAL_REQUEST: (CCR_I, CCA_I),
            E_CC_REQUEST_TYPE_UPDATE_REQUEST: (CCR_U, CCA_U),
            E_CC_REQUEST_TYPE_TERMINATION_REQUEST: (CCR_T, CCA_T)
        }
        
        cc_request_type = getattr(message, 'cc_request_type', None) if hasattr(message, 'cc_request_type') else None
        
        if cc_request_type is not None and cc_request_type in cc_type_mapping:
            return cc_type_mapping[cc_request_type][0 if isinstance(message, CreditControlRequest) else 1]
        
        if isinstance(message, CreditControlRequest):
            return "CCR"
        else:
            if hasattr(message, 'result_code') and message.result_code != E_RESULT_CODE_DIAMETER_SUCCESS:
                return "CCA-ERROR"
            return "CCA"

    message_type_mapping = {
        ReAuth: (RAR, RAA),
        AbortSession: (ASR, ASA),
        SpendingLimit: (SLR, SLA),
        SpendingStatusNotification: (SSNR, SSNA),
        DeviceWatchdog: (DWR, DWA),
        CapabilitiesExchange: (CER, CEA),
        SessionTermination: (STR, STA),
        Aa: (AAR, AAA),
        DisconnectPeer: (DPR, DPA)
    }

    for msg_type, (req_name, ans_name) in message_type_mapping.items():
        if isinstance(message, msg_type):
            return req_name if is_request else ans_name

    return f"{diameter_message.message.header.application_id},{diameter_message.message.header.command_code}"

