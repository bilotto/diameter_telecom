from .. import Subscriber
from ..message import DiameterMessage, Message
from ..constants import *
from typing import List, Optional
import time
from dataclasses import dataclass, field
import logging
logger = logging.getLogger(__name__)

@dataclass
class DiameterSession:
    session_id: str
    active: bool = field(default=False)
    error: bool = field(default=False)
    ended: bool = field(default=False)
    messages: List[DiameterMessage] = field(default_factory=list)
    start_time: Optional[str] = field(default=None)
    end_time: Optional[str] = field(default=None)
    subscriber: Optional[Subscriber] = field(default=None)

    def __post_init__(self):
        if not isinstance(self.session_id, str):
            raise ValueError("session_id must be a string")

    def __hash__(self) -> int:
        return hash(self.session_id)
    
    def __eq__(self, other) -> bool:
        return self.session_id == other.session_id

    def start(self, timestamp: str = None):
        if not self.active:
            if timestamp:
                self.start_time = timestamp
            else:
                self.start_time = str(time.time())
            self.active = True
            logger.info(f"Session {self.session_id} started at {self.start_time}")

    def end(self, timestamp: str = None):
        if self.active:
            if timestamp:
                self.end_time = timestamp
            else:
                self.end_time = str(time.time())
            self.active = False
            self.ended = True
            logger.info(f"Session {self.session_id} ended at {self.end_time}")

    def add_message(self, message) -> DiameterMessage:
        if isinstance(message, DiameterMessage):
            dm = message
        elif isinstance(message, Message):
            dm = DiameterMessage(message)
        else:
            raise ValueError("message must be an instance of Message or DiameterMessage")
        if not dm.timestamp:
            dm.timestamp = time.time()
        self.messages.append(dm)
        return dm

    def get_messages(self) -> List[DiameterMessage]:
        return self.messages
    
    def set_subscriber(self, subscriber: Subscriber):
        if not isinstance(subscriber, Subscriber):
            raise ValueError("subscriber must be an instance of Subscriber")
        self.subscriber = subscriber

    @property
    def last_message(self):
        if self.messages:
            return self.messages[-1]
        return None
    
    @property
    def n_messages(self):
        return len(self.messages)
    
    @property
    def duration(self):
        if self.start_time and self.end_time:
            return int(float(self.end_time) - float(self.start_time))
        elif self.start_time:
            return int(time.time() - float(self.start_time))
        return None

    def dump_messages(self, output_file: str):
        """Dump all messages in the session to a file."""
        with open(output_file, 'w') as f:
            for message in self.messages:
                f.write(message.dump() + '\n')
        logger.info(f"Messages dumped to {output_file}")

    def dump_hex_strings(self, output_file: str):
        """Dump all messages in the session as hex strings to a file."""
        with open(output_file, 'w') as f:
            for message in self.messages:
                f.write(message.hex_string + '\n')
        logger.info(f"Hex strings dumped to {output_file}")

    def to_json(self) -> dict:
        """
        Convert DiameterSession to JSON-serializable dictionary.
        
        Returns:
            dict: JSON-serializable representation of the session
        """
        try:
            session_data = {
                "session_id": self.session_id,
                "active": self.active,
                "error": self.error,
                "ended": self.ended,
                "start_time": self.start_time,
                "end_time": self.end_time,
                "duration": self.duration,
                "message_count": self.n_messages,
                # "session_type": self.__class__.__name__
            }
            
            # # Add session-specific attributes for Gx sessions
            # if hasattr(self, "framed_ip_address"):
            #     framed_ip = getattr(self, "framed_ip_address", None)
            #     # Convert bytes to string if necessary
            #     if isinstance(framed_ip, bytes):
            #         try:
            #             import socket
            #             session_data["framed_ip_address"] = socket.inet_ntoa(framed_ip)
            #         except Exception:
            #             session_data["framed_ip_address"] = framed_ip.hex()
            #     else:
            #         session_data["framed_ip_address"] = framed_ip
                    
            # if hasattr(self, "framed_ipv6_prefix"):
            #     framed_ipv6 = getattr(self, "framed_ipv6_prefix", None)
            #     # Convert bytes to string if necessary
            #     if isinstance(framed_ipv6, bytes):
            #         try:
            #             import ipaddress
            #             # Try to decode as IPv6 prefix
            #             if len(framed_ipv6) >= 2:
            #                 prefix_length = framed_ipv6[1]
            #                 ipv6_bytes = framed_ipv6[2:].ljust(16, b'\x00')
            #                 ipv6_address = ipaddress.IPv6Address(ipv6_bytes)
            #                 session_data["framed_ipv6_prefix"] = f"{ipv6_address}/{prefix_length}"
            #             else:
            #                 session_data["framed_ipv6_prefix"] = framed_ipv6.hex()
            #         except Exception:
            #             session_data["framed_ipv6_prefix"] = framed_ipv6.hex()
            #     else:
            #         session_data["framed_ipv6_prefix"] = framed_ipv6
                    
            # if hasattr(self, "bearer_id"):
            #     bearer_id = getattr(self, "bearer_id", None)
            #     # Convert bytes to string if necessary
            #     if isinstance(bearer_id, bytes):
            #         session_data["bearer_id"] = bearer_id.hex()
            #     else:
            #         session_data["bearer_id"] = bearer_id
                    
            # if hasattr(self, "charging_rule_name"):
            #     charging_rule = getattr(self, "charging_rule_name", None)
            #     # Convert bytes to string if necessary
            #     if isinstance(charging_rule, bytes):
            #         session_data["charging_rule_name"] = charging_rule.decode('utf-8', errors='replace')
            #     else:
            #         session_data["charging_rule_name"] = charging_rule
            
            # Add subscriber reference if available
            if self.subscriber:
                session_data["subscriber"] = self.subscriber.to_json()
            
            # Add sample messages (limit to 5 for performance)
            # session_data["sample_messages"] = [
            #     msg.to_json() if hasattr(msg, 'to_json') else {
            #         "session_id": getattr(msg, "session_id", None),
            #         "cmd_code": getattr(msg, "cmd_code", None),
            #         "app_id": getattr(msg, "app_id", None),
            #         "is_request": getattr(msg, "is_request", None),
            #         "timestamp": getattr(msg, "timestamp", None),
            #         "name": getattr(msg, "name", None),
            #         "result_code": getattr(msg, "result_code", None),
            #         "pcap_filepath": getattr(msg, "pcap_filepath", None)
            #     }
            #     for msg in self.messages[:5]
            # ]
            session_data['messages'] = [msg.to_json() for msg in self.messages]
            
            return session_data
            
        except Exception as e:
            logger.exception(f"Failed to serialize session {self.session_id}")
            return {
                "session_id": self.session_id,
                "error": f"Serialization failed: {str(e)}"
            }