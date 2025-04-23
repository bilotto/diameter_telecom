from diameter.message.commands import *
from diameter.message.avp.grouped import *
from diameter.message import Message
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
    

    def set_timestamp(self, timestamp):
        self.timestamp = timestamp

    def set_subscriber(self, subscriber: Subscriber):
        if not isinstance(subscriber, Subscriber):
            raise ValueError("Subscriber must be an instance of Subscriber")
        self.subscriber = subscriber

    @property
    def name(self):
        return name_diameter_message(self)
    
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
    
    
    def dump_hex_string(self, file_full_path):
        with open(file_full_path, 'w') as f:
            f.write(self.hex_string)
        logger.info(f"Hex string written to {file_full_path}")



def name_diameter_message(diameter_message: DiameterMessage):
    message = diameter_message.message
    if isinstance(message, CreditControl):
        if isinstance(message, CreditControlRequest):
            cc_request_type = message.cc_request_type
            if cc_request_type and cc_request_type == E_CC_REQUEST_TYPE_INITIAL_REQUEST:
                return CCR_I
            elif cc_request_type and cc_request_type == E_CC_REQUEST_TYPE_UPDATE_REQUEST:
                return CCR_U
            elif cc_request_type and cc_request_type == E_CC_REQUEST_TYPE_TERMINATION_REQUEST:
                return CCR_T
        elif isinstance(message, CreditControlAnswer):
            cc_request_type = message.cc_request_type
            if cc_request_type and cc_request_type == E_CC_REQUEST_TYPE_INITIAL_REQUEST:
                return CCA_I
            elif cc_request_type and cc_request_type == E_CC_REQUEST_TYPE_UPDATE_REQUEST:
                return CCA_U
            elif cc_request_type and cc_request_type == E_CC_REQUEST_TYPE_TERMINATION_REQUEST:
                return CCA_T
    elif isinstance(message, ReAuth):
        return RAR if message.header.is_request else RAA
    elif isinstance(message, AbortSession):
        return ASR if message.header.is_request else ASA
    elif isinstance(message, SpendingLimit):
        return SLR if message.header.is_request else SLA
    elif isinstance(message, SpendingStatusNotification):
        return SSNR if message.header.is_request else SSNA
    elif isinstance(message, DeviceWatchdog):
        return DWR if message.header.is_request else DWA
    elif isinstance(message, CapabilitiesExchange):
        return CER if message.header.is_request else CEA
    elif isinstance(message, SessionTermination):
        return STR if message.header.is_request else STA
    elif isinstance(message, Aa):
        return AAR if message.header.is_request else AAA
    
    return None

