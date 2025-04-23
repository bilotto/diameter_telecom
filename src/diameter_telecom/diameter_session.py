from .subscriber import Subscriber
from .diameter_message import DiameterMessage, Message
from typing import List
import time

class DiameterSession:
    subscriber: Subscriber
    session_id: str
    active: bool
    messages: List[DiameterMessage]
    start_time: str
    end_time: str

    def __init__(self, subscriber: Subscriber, session_id: str):
        if not isinstance(subscriber, Subscriber):
            raise ValueError("Subscriber must be an instance of Subscriber")
        if not isinstance(session_id, str):
            raise ValueError("session_id must be a string")
        self.subscriber = subscriber
        self.session_id = session_id
        self.active = False
        self.error = False
        self.messages = []
        #
        self.start_time = None
        self.end_time = None

    def __hash__(self) -> int:
        return hash(self.session_id)
    
    def __eq__(self, other) -> bool:
        return self.session_id == other.session_id
       
    def set_start_time(self, start_time: str):
        self.start_time = start_time
        self.active = True

    def start(self):
        if not self.active:
            self.set_start_time(str(time.time()))

    def end(self):
        if self.active:
            self.set_end_time(str(time.time()))

    def set_end_time(self, end_time: str):
        self.end_time = end_time
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

    def get_messages(self):
        return self.messages

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


class GxSession(DiameterSession):
    session_id: str
    framed_ip_address: str
    apn: str

    def __init__(self,
                 subscriber,
                 session_id: str,
                 framed_ip_address: str,
                 apn: str = None,):
        super().__init__(subscriber, session_id)
        self.framed_ip_address = framed_ip_address
        self.apn = apn
        
