from diameter.message.commands import *
from diameter.message.avp.grouped import *
from diameter.message import Message, dump
from .constants import *
from . import Subscriber
import datetime
import logging

logger = logging.getLogger(__name__)

class DiameterMessage:
    """
    Represents a Diameter protocol message with extended functionality.
    
    This class wraps the base Diameter message implementation with additional
    functionality for telecom-specific operations. It provides methods to
    handle message attributes, subscriber information, and message formatting.
    
    Attributes:
        message: The underlying Diameter message object
        timestamp: Message timestamp for tracking when the message was processed
        subscriber: Associated subscriber information
        pkt_number: Packet number for message tracking
        pcap_filepath: Path to the PCAP file containing this message
        framed_ip_address: Framed IP address associated with the message
        framed_ipv6_prefix: Framed IPv6 prefix associated with the message
        mcc_mnc: Mobile Country Code and Mobile Network Code
        apn: Access Point Name associated with the message
    """
    
    def __init__(self, obj):
        """
        Initialize a DiameterMessage instance.
        
        Args:
            obj: Either a hex string representation of the message or a Message instance
            
        Raises:
            ValueError: If an invalid hex string is provided
            TypeError: If obj is neither a string nor a Message instance
        """
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
            'framed_ipv6_prefix': None,
            'sgsn_mcc_mnc': None,
            'called_station_id': None
        }

    def __getattr__(self, name):
        """
        Custom attribute getter to handle both message and custom attributes.
        
        Args:
            name: Name of the attribute to get
            
        Returns:
            The requested attribute value or None if not found
        """
        if name in self._attributes:
            return self._attributes[name]
        elif hasattr(self.message, name):
            return getattr(self.message, name)
        else:
            return None

    def __setattr__(self, name, value):
        """
        Custom attribute setter to handle both message and custom attributes.
        
        Args:
            name: Name of the attribute to set
            value: Value to set for the attribute
            
        Raises:
            ValueError: If trying to set a subscriber that is not a Subscriber instance
        """
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
        """
        Get the name of the Diameter message.
        
        Returns:
            str: The name of the message (e.g., CCR-I, CCA-I, etc.)
        """
        return name_diameter_message(self)
    
    @property
    def message_name(self):
        """
        Get the message name (alias for name property).
        
        Returns:
            str: The name of the message
        """
        return self.name
    
    @property
    def app_id(self):
        """
        Get the application ID from the message header.
        
        Returns:
            int: The application ID
        """
        return self.message.header.application_id
    
    @property
    def is_request(self):
        """
        Check if the message is a request message.
        
        Returns:
            bool: True if the message is a request, False if it's an answer
        """
        return self.message.header.is_request

    @property
    def hex_string(self):
        """
        Get the message as a hex string.
        
        Returns:
            str: The message in hexadecimal format
        """
        return self.message.as_bytes().hex()
    
    @property
    def msisdn(self):
        """
        Get the MSISDN from the associated subscriber.
        
        Returns:
            str or None: The MSISDN if a subscriber is associated, None otherwise
        """
        return self.subscriber.msisdn if self.subscriber else None
    
    @property
    def imsi(self):
        """
        Get the IMSI from the associated subscriber.
        
        Returns:
            str or None: The IMSI if a subscriber is associated, None otherwise
        """
        return self.subscriber.imsi if self.subscriber else None
    
    @property
    def time(self):
        """
        Get the formatted timestamp of the message.
        
        Returns:
            str or None: Formatted timestamp string if timestamp exists, None otherwise
        """
        if self.timestamp:
            return datetime.datetime.fromtimestamp(float(self.timestamp)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return None
    
    @property
    def hop_by_hop_id(self):
        """
        Get the hop-by-hop identifier from the message header.
        
        Returns:
            int: The hop-by-hop identifier
        """
        return self.message.header.hop_by_hop_identifier
    
    @property
    def end_to_end_id(self):
        """
        Get the end-to-end identifier from the message header.
        
        Returns:
            int: The end-to-end identifier
        """
        return self.message.header.end_to_end_identifier
    
    @property
    def apn(self):
        """
        Get the APN from the called station ID.
        
        Returns:
            str or None: The APN if called station ID exists, None otherwise
        """
        return self.called_station_id
    
    def dump_hex_string(self, file_full_path):
        """
        Dump the message as a hex string to a file.
        
        Args:
            file_full_path (str): Path to the output file
        """
        with open(file_full_path, 'w') as f:
            f.write(self.hex_string)
        logger.info(f"Hex string written to {file_full_path}")

    def dump(self):
        """
        Get a string representation of the message.
        
        Returns:
            str: Formatted message dump
        """
        return dump(self.message)
    
    def __repr__(self):
        return f"{self.time},{self.name}"
    
    def __eq__(self, other):
        return self.hop_by_hop_id == other.hop_by_hop_id and self.end_to_end_id == other.end_to_end_id and self.is_request == other.is_request
    
    def __hash__(self):
        return hash((self.hop_by_hop_id, self.end_to_end_id, self.is_request))


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

