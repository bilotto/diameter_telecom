from .subscriber import Subscriber
from .diameter_message import DiameterMessage, Message
from .constants import *
from typing import List
import time

class DiameterSession:
    session_id: str
    active: bool
    messages: List[DiameterMessage]
    start_time: str
    end_time: str

    def __init__(self, session_id: str):
        if not isinstance(session_id, str):
            raise ValueError("session_id must be a string") 
        self.session_id = session_id
        self.active = False
        self.error = False
        self.messages = []
        self.start_time = None
        self.end_time = None
        self.subscriber = None

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

    def end(self, timestamp: str = None):
        if self.active:
            if timestamp:
                self.end_time = timestamp
            else:
                self.end_time = str(time.time())
            self.active = False

    def add_message(self, message):
        if not isinstance(message, Message) and not isinstance(message, DiameterMessage):
            raise ValueError("message must be an instance of Message or DiameterMessage")
        if isinstance(message, DiameterMessage):
            diameter_message = message
        elif isinstance(message, Message):
            diameter_message = DiameterMessage(message)
        else:
            raise ValueError("message must be an instance of Message or DiameterMessage")
        self.messages.append(diameter_message)

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

class SySession(DiameterSession):
    session_id: str
    gx_session_id: str

    def __init__(self, session_id: str):
        super().__init__(session_id)
        self.gx_session_id = None

    def set_gx_session_id(self, gx_session_id: str):
        self.gx_session_id = gx_session_id

    def add_message(self, message):
        super().add_message(message)
        if message.name == SLR:
            if message.timestamp:
                self.start(message.timestamp)
            else:
                self.start()
        elif message.name == STR:
            if message.timestamp:
                self.end(message.timestamp)
            else:
                self.end()

class RxSession(DiameterSession):
    session_id: str

    def __init__(self, session_id: str):
        super().__init__(session_id)
        self.gx_session_id = None

    def set_gx_session_id(self, gx_session_id: str):
        self.gx_session_id = gx_session_id

    def add_message(self, message):
        super().add_message(message)
        if message.name == AAR:
            if message.timestamp:
                self.start(message.timestamp)
            else:
                self.start()
        elif message.name == STR:
            if message.timestamp:
                self.end(message.timestamp)
            else:
                self.end()


class GxSession(DiameterSession):
    session_id: str
    _framed_ip_address: str
    _framed_ipv6_prefix: str
    apn: str
    mcc_mnc: str

    def __init__(self, session_id: str):
        super().__init__(session_id)
        self._framed_ip_address = None
        self._framed_ipv6_prefix = None
        self.apn = None
        self.mcc_mnc = None

    @property
    def framed_ip_address(self):
        return self._framed_ip_address or self._framed_ipv6_prefix

    def set_mcc_mnc(self, mcc_mnc: str):
        self.mcc_mnc = mcc_mnc

    def set_framed_ip_address(self, framed_ip_address: str):
        self._framed_ip_address = framed_ip_address

    def set_framed_ipv6_prefix(self, framed_ipv6_prefix: str):
        self._framed_ipv6_prefix = framed_ipv6_prefix

    def set_apn(self, apn: str):
        self.apn = apn

    def add_message(self, message: DiameterMessage):
        super().add_message(message)
        if message.name == CCR_I:
            if message.timestamp:
                self.start(message.timestamp)
            else:
                self.start()
        elif message.name == CCR_T:
            if message.timestamp:
                self.end(message.timestamp)
            else:
                self.end()
