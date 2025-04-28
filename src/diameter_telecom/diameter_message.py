from diameter.message.commands import *
from diameter.message.avp.grouped import *
from diameter.message import Message, dump
from .constants import *
from .subscriber import Subscriber

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
        
        self.timestamp = None
        self.subscriber = None
        self.pkt_number = None
        self.pcap_filepath = None
        self.framed_ip_address = None
        self.mcc_mnc = None
        self.apn = None


    def set_timestamp(self, timestamp):
        self.timestamp = timestamp

    def set_subscriber(self, subscriber: Subscriber):
        if not isinstance(subscriber, Subscriber):
            raise ValueError("Subscriber must be an instance of Subscriber")
        self.subscriber = subscriber
    
    def set_pcap_filepath(self, pcap_filepath: str):
        self.pcap_filepath = pcap_filepath

    def set_pkt_number(self, pkt_number: int):
        self.pkt_number = pkt_number

    def set_framed_ip_address(self, framed_ip_address: str):
        self.framed_ip_address = framed_ip_address

    def set_mcc_mnc(self, mcc_mnc: str):
        self.mcc_mnc = mcc_mnc

    def set_apn(self, apn: str):
        self.apn = apn

    

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
    def session_id(self):
        return self.message.session_id
    
    @property
    def is_request(self):
        return self.message.header.is_request

    @property
    def hex_string(self):
        return self.message.as_bytes().hex()
    
    @property
    def msisdn(self):
        return self.subscriber.msisdn
    
    @property
    def imsi(self):
        return self.subscriber.imsi
    
    @property
    def result_code(self):
        if hasattr(self.message, 'result_code'):
            return self.message.result_code
        else:
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

