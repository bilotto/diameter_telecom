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
            logger.info(f"Session {self.session_id} ended at {self.end_time}")

    def add_message(self, message):
        if not isinstance(message, Message) and not isinstance(message, DiameterMessage):
            raise ValueError("message must be an instance of Message or DiameterMessage")
        if isinstance(message, DiameterMessage):
            diameter_message = message
        elif isinstance(message, Message):
            diameter_message = DiameterMessage(message)
        else:
            raise ValueError("message must be an instance of Message or DiameterMessage")
        if diameter_message in self.messages:
            return None
        self.messages.append(diameter_message)
        return diameter_message

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
