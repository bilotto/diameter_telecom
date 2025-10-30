from diameter.message import Message, dump
from .diameter_layer import Message, dump
from .constants import *
import datetime
import logging
import time

logger = logging.getLogger(__name__)

def convert_timestamp(timestamp: str) -> str:
    return datetime.datetime.fromtimestamp(float(timestamp), tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

class DiameterMessage:
    def __init__(self, obj: Message | str):
        if isinstance(obj, Message):
            message = obj
            self.message_bytes = message.as_bytes()
            self.hop_by_hop_id = message.header.hop_by_hop_identifier
            self.end_to_end_id = message.header.end_to_end_identifier
            self.is_request = message.header.is_request
            self.app_id = message.header.application_id
            self.cmd_code = message.header.command_code

        elif isinstance(obj, str):
            try:
                hex_string = obj.strip().replace(':', '')
                message_bytes = bytes.fromhex(hex_string)
                message: Message = Message.from_bytes(message_bytes)
                self.message_bytes = message_bytes
                self.hop_by_hop_id = message.header.hop_by_hop_identifier
                self.end_to_end_id = message.header.end_to_end_identifier
                self.is_request = message.header.is_request
                self.app_id = message.header.application_id
                self.cmd_code = message.header.command_code
            except ValueError:
                raise ValueError("Invalid hex string provided.")
        else:
            raise TypeError(f"Parameter must be a hex string or a Message instance. Provided: {obj},{type(obj)}")
        
        self.timestamp = time.time()
        self.result_code = None
        self.cc_request_type = None
        self.session_id = None
        if hasattr(message, 'result_code'):
            self.result_code = message.result_code
        if hasattr(message, 'cc_request_type'):
            self.cc_request_type = message.cc_request_type
        if hasattr(message, 'session_id'): 
            self.session_id = message.session_id

        self._message = message

    @property
    def name(self):
        return name_diameter_message(self.is_request, self.cmd_code, self.cc_request_type)

    def __repr__(self):
        return f"{self.time},{self.name}"

    @property
    def message(self) -> Message:
        if self._message is None:
            self._message = Message.from_bytes(self.message_bytes)
        return self._message

    def clear_message(self):
        self._message = None
    

    @property
    def hex_string(self):
        return self.message_bytes.hex()
        
    @property
    def processing_time(self):
        """Processing time in milliseconds (calculated from microseconds)"""
        if self.processing_time_microseconds is not None:
            return self.processing_time_microseconds / 1000.0
        return None
        
    @property
    def time(self):
        if self.timestamp:
            return datetime.datetime.fromtimestamp(float(self.timestamp), tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return None
    
    @property
    def header(self):
        return self.message.header
    
    def dump_hex_string(self, file_full_path):
        with open(file_full_path, 'w') as f:
            f.write(self.hex_string)
        logger.info(f"Hex string written to {file_full_path}")

    def dump(self):
        return dump(self.message)
    
    def __repr__(self):
        return f"{self.time},{self.name}"
    
    def __eq__(self, other):
        return self.hop_by_hop_id == other.hop_by_hop_id and self.end_to_end_id == other.end_to_end_id and self.is_request == other.is_request
    
    def __hash__(self):
        return hash((self.hop_by_hop_id, self.end_to_end_id, self.is_request))
    
    def set_message_attribute(self, name, value):
        if not hasattr(self.message, name):
            raise ValueError(f"Attribute {name} not found in message")
        setattr(self.message, name, value)

    def set_message_header_attribute(self, name, value):
        if not hasattr(self.message.header, name):
            raise ValueError(f"Attribute {name} not found in message header")
        setattr(self.message.header, name, value)

    def to_dict(self) -> dict:
        try:
            message_data = dict()
            message_data['is_request'] = self.is_request
            message_data['name'] = self.name
            message_data['time'] = self.time
            if hasattr(self.message, 'result_code') and self.message.result_code is not None:
                message_data['result_code'] = self.message.result_code
            return message_data
            
        except Exception as e:
            logger.exception(f"Failed to serialize DiameterMessage")
            return {
                "session_id": getattr(self, 'session_id', None),
                "name": getattr(self, 'name', None),
                "error": f"Serialization failed: {str(e)}"
            }


def name_diameter_message(is_request, cmd_code, cc_request_type):
    if cmd_code == CMD_CREDIT_CONTROL:
        if cc_request_type == E_CC_REQUEST_TYPE_INITIAL_REQUEST:
            return "CCR-I" if is_request else "CCA-I"
        elif cc_request_type == E_CC_REQUEST_TYPE_UPDATE_REQUEST:
            return "CCR-U" if is_request else "CCA-U"
        elif cc_request_type == E_CC_REQUEST_TYPE_TERMINATION_REQUEST:
            return "CCR-T" if is_request else "CCA-T"
        else:
            return "CCR" if is_request else "CCA"
    elif cmd_code == CMD_RE_AUTH:
        return "RAR" if is_request else "RAA"
    elif cmd_code == CMD_ABORT_SESSION:
        return "ASR" if is_request else "ASA"
    elif cmd_code == CMD_SPENDING_LIMIT:
        return "SLR" if is_request else "SLA"
    elif cmd_code == CMD_SPENDING_STATUS_NOTIFICATION:
        return "SSNR" if is_request else "SSNA"
    elif cmd_code == CMD_DEVICE_WATCHDOG:
        return "DWR" if is_request else "DWA"
    elif cmd_code == CMD_CAPABILITIES_EXCHANGE:
        return "CER" if is_request else "CEA"
    elif cmd_code == CMD_SESSION_TERMINATION:
        return "STR" if is_request else "STA"
    elif cmd_code == CMD_AA:
        return "AAR" if is_request else "AAA"
    elif cmd_code == CMD_DISCONNECT_PEER:
        return "DPR" if is_request else "DPA"
    else:
        return f"{cmd_code}"

from typing import List, Optional
from typing_extensions import Tuple
from dataclasses import dataclass, field

@dataclass
class DiameterMessages:
    messages: List[DiameterMessage] = field(default_factory=list)
    messages_pairs: List[Tuple[DiameterMessage, DiameterMessage]] = field(default_factory=list)
    _last_end_to_end_id: Optional[str] = field(default=None) # end_to_end_id

    def __iter__(self):
        return iter(self.messages)

    def __contains__(self, message: DiameterMessage):
        return message in self.messages

    def __len__(self):
        return len(self.messages)

    def __getitem__(self, index):
        return self.messages[index]

    def __setitem__(self, index, value):
        self.messages[index] = value

    def __delitem__(self, index):
        del self.messages[index]

    def __iter__(self):
        return iter(self.messages)

    def __next__(self):
        return next(self.messages)

    def append(self, message: DiameterMessage):
        if isinstance(message, Message):
            message = DiameterMessage(message)
        logger.debug(message)
        if len(self.messages) == 0:
            logger.debug(f"First message: {message}")
            if not message.is_request:
                logger.error(f"Starting DiameterMessages with a message that is not a request: {message.name}")
        else:
            if self._last_end_to_end_id and message.end_to_end_id != self._last_end_to_end_id:
                logger.error(f"Adding message with different end_to_end_id: {message.name}")
        self.messages.append(message)
        if message.is_request:
            self._last_end_to_end_id = message.end_to_end_id
        else:
            self._last_end_to_end_id = None