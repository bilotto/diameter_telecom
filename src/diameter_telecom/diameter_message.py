from diameter.message.commands import *
from diameter.message.avp.grouped import *
from diameter.message import Message, dump
from .constants import *
from .subscriber import Subscriber
import datetime

logger = logging.getLogger(__name__)

class DiameterMessage:
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
        
        # Initialize default attributes
        self._attributes = {
            'timestamp': None,
            'subscriber': None,
            'pkt_number': None,
            'pcap_filepath': None,
            'framed_ip_address': None,
            'mcc_mnc': None,
            'apn': None
        }

    def __getattr__(self, name):
        if name in self._attributes:
            return self._attributes[name]
        elif hasattr(self.message, name):
            return getattr(self.message, name)
        else:
            return None

    def __setattr__(self, name, value):
        if name == 'message' or name == '_attributes':
            # Handle special attributes directly
            super().__setattr__(name, value)
        elif name == 'subscriber' and value is not None:
            # Special handling for subscriber to ensure type checking
            if not isinstance(value, Subscriber):
                raise ValueError("Subscriber must be an instance of Subscriber")
            self._attributes[name] = value
        else:
            # Handle all other attributes through the _attributes dict
            self._attributes[name] = value

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
            return datetime.datetime.fromtimestamp(float(self.timestamp)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return None
    
    def dump_hex_string(self, file_full_path):
        with open(file_full_path, 'w') as f:
            f.write(self.hex_string)
        logger.info(f"Hex string written to {file_full_path}")

    def dump(self):
        return dump(self.message)



def name_diameter_message(diameter_message: DiameterMessage) -> str | None:
    """
    Get the name of a diameter message based on its type and request/response status.
    
    Args:
        diameter_message: The DiameterMessage instance to name
        
    Returns:
        str: The message name or None if not recognized
    """
    message = diameter_message.message
    is_request = message.header.is_request

    # Handle Credit Control messages separately due to additional type check
    if isinstance(message, CreditControl):
        cc_type_mapping = {
            E_CC_REQUEST_TYPE_INITIAL_REQUEST: (CCR_I, CCA_I),
            E_CC_REQUEST_TYPE_UPDATE_REQUEST: (CCR_U, CCA_U),
            E_CC_REQUEST_TYPE_TERMINATION_REQUEST: (CCR_T, CCA_T)
        }
        cc_request_type = message.cc_request_type
        if cc_request_type in cc_type_mapping:
            return cc_type_mapping[cc_request_type][0 if isinstance(message, CreditControlRequest) else 1]
        return None

    # Map message types to their request/answer names
    message_type_mapping = {
        ReAuth: (RAR, RAA),
        AbortSession: (ASR, ASA),
        SpendingLimit: (SLR, SLA),
        SpendingStatusNotification: (SSNR, SSNA),
        DeviceWatchdog: (DWR, DWA),
        CapabilitiesExchange: (CER, CEA),
        SessionTermination: (STR, STA),
        Aa: (AAR, AAA)
    }

    # Get the appropriate name based on message type and request/answer status
    for msg_type, (req_name, ans_name) in message_type_mapping.items():
        if isinstance(message, msg_type):
            return req_name if is_request else ans_name

    return None

