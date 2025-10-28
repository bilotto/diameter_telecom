import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from .. import Subscriber
from ..constants import *
from ..message import DiameterMessage, Message, convert_timestamp, DiameterMessages

logger = logging.getLogger("diameter_telecom.session")

@dataclass
class DiameterSession:
    session_id: str
    active: bool = field(default=False)
    error: bool = field(default=False)
    ended: bool = field(default=False)
    messages: DiameterMessages = field(default_factory=DiameterMessages, repr=True)
    start_time: Optional[str] = field(default=None)
    end_time: Optional[str] = field(default=None)
    subscriber: Optional[Subscriber] = field(default=None)
    bound_sessions: Dict[int, List[str]] = field(default_factory=lambda: {app_id: [] for app_id in [APP_3GPP_GX, APP_3GPP_RX, APP_3GPP_SY]})
    last_result_code: Optional[int] = field(default=None)
    _avps: Dict[str, Any] = field(default_factory=dict, repr=False)
    logger: logging.Logger = field(default=logger, repr=False)
    app_id: Optional[int] = field(default=None, repr=False)
    origin_host: Optional[str] = field(default=None)
    origin_realm: Optional[str] = field(default=None)
    abort: Optional[bool] = field(default=None, init=False)

    @property
    def avps(self) -> Dict[str, Any]:
        return self._avps

    def add_avps(self, message: Message):
        for key, value in self.avps.items():
            if hasattr(message, key):
                self.logger.debug(f"Adding AVPS (session): {key} = {value}")
                setattr(message, key, value)
        return message

    def add_avp(self, key: str, value: Any):
        self._avps[key] = value

    def add_bound_session(self, app_id: int, session_id: str):
        self.bound_sessions[app_id].append(session_id)

    def __post_init__(self):
        if not isinstance(self.session_id, str):
            raise ValueError("session_id must be a string")

    def __hash__(self) -> int:
        return hash(self.session_id)
    
    def __eq__(self, other) -> bool:
        return self.session_id == other.session_id
    
    def __str__(self) -> str:
        """String representation for logging and display."""
        return f"{self.__class__.__name__}(session_id={self.session_id}, active={self.active}, ended={self.ended})"

    def activate(self):
        self.active = True

    def start(self, timestamp: str = None):
        if not self.active:
            if timestamp:
                self.start_time = timestamp
            else:
                self.start_time = str(time.time())

    def end(self, timestamp: str = None):
        if self.active:
            if timestamp:
                self.end_time = timestamp
            else:
                self.end_time = str(time.time())
            self.active = False
            self.ended = True

    def add_message(self, message) -> DiameterMessage:
        if isinstance(message, DiameterMessage):
            dm = message
        elif isinstance(message, Message):
            dm = DiameterMessage(message)
        else:
            raise ValueError("message must be an instance of Message or DiameterMessage")
        if not dm.end_to_end_id:
            logger.warning(f"[{self.session_id}] (add_message) Message {dm.name} has no end-to-end identifier. This is not allowed.")
            pass
        if self.n_messages == 0:
            if not dm.is_request:
                logger.error(f"[{self.session_id}] (add_message) Message {dm.name} is not a request. This is not allowed.")
                return None
            self.origin_host = dm.message.origin_host.decode()
            self.origin_realm = dm.message.origin_realm.decode()
        # if not dm.timestamp:
        #     dm.timestamp = time.time()
        # dm.session_id = None
        if dm.result_code:
            self.last_result_code = dm.result_code
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

    def to_dict(self) -> dict:
        try:
            session_data = dict()
            session_data["session_id"] = self.session_id
            session_data["active"] = self.active
            session_data["error"] = self.error
            session_data["ended"] = self.ended
            if self.start_time:
                session_data["start_time"] = convert_timestamp(self.start_time)
            if self.end_time:
                session_data["end_time"] = convert_timestamp(self.end_time)
            if self.duration:
                session_data["duration"] = self.duration
            # session_data["message_count"] = self.n_messages

            # "session_type": self.__class__.__name__
            
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
                session_data["msisdn"] = self.subscriber.msisdn
            
            # Add sample messages (limit to 5 for performance)
            # session_data["sample_messages"] = [
            #     msg.to_dict() if hasattr(msg, 'to_json') else {
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
            session_data['messages'] = [msg.to_dict() for msg in self.messages]
            
            return session_data
            
        except Exception as e:
            logger.exception(f"Failed to serialize session {self.session_id}")
            return {
                "session_id": self.session_id,
                "error": f"Serialization failed: {str(e)}"
            }