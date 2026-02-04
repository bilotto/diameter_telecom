from dataclasses import dataclass, field
from typing import List, Dict, Optional
import threading
from diameter.message.avp.grouped import SubscriptionId
from .constants import *
from .message import DiameterMessage
from diameter.message import Message
import logging
logger = logging.getLogger(__name__)

@dataclass
class Subscriber:
    """
    Represents a mobile subscriber with their identification information.
    
    This class stores the essential identification information for a mobile subscriber
    in a telecommunications network. It includes the standard identifiers used in
    mobile networks for subscriber identification and device tracking.
    
    Attributes:
        msisdn (str): Mobile Subscriber Integrated Services Digital Network Number.
                     This is the phone number of the subscriber.
        imsi (str): International Mobile Subscriber Identity. A unique identifier
                   for the subscriber in the mobile network.
        sip_uri (str, optional): Session Initiation Protocol Uniform Resource Identifier.
                               Used for SIP-based communication.
        nai (str, optional): Network Access Identifier. Used for network access
                           authentication and identification.
        private_id (str, optional): Private identifier for the subscriber, used in
                                  certain authentication scenarios.
        imei (str, optional): International Mobile Equipment Identity. A unique
                             identifier for the subscriber's mobile device.
        apn (APN, optional): Access Point Name associated with the subscriber.
        messages (List[DiameterMessage]): List of all Diameter messages associated with this subscriber.
    """
    msisdn: str
    imsi: str = field(default=None, repr=False)
    sip_uri: str = field(default=None, repr=False)
    nai: str = field(default=None, repr=False)
    private_id: str = field(default=None, repr=False)
    imei: str = field(default=None, repr=False)
    apn: str = field(default=None, repr=False)
    messages: List[DiameterMessage] = field(default_factory=list, repr=False)
    sessions: Dict[int, List[str]] = field(default_factory=dict, repr=True)
    _sessions_lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)
    _avps: Dict[str, str] = field(default_factory=dict, repr=False)
    carrier_name: str = field(default=None, repr=False)
    # We will replace sessions with sessions
    policy_counters: Dict[str, str] = field(default_factory=dict, repr=False)

    @property
    def session_ids(self) -> Dict[int, List[str]]:
        return self.sessions

    @property
    def avps(self) -> Dict[str, str]:
        self._avps['subscription_id'] = self.get_subscription_id()
        return self._avps

    def __post_init__(self):
        """
        Post-initialization hook to ensure proper type conversion of all fields.
        
        Converts all non-None attributes to strings to ensure consistent type handling.
        """
        for attr in ['msisdn', 'imsi', 'sip_uri', 'nai', 'private_id', 'imei']:
            val = getattr(self, attr)
            if val is not None:
                setattr(self, attr, str(val))

    # def __repr__(self) -> str:
    #     fields = []
    #     for attr in ['msisdn', 'imsi', 'sip_uri', 'nai', 'private_id', 'imei', 'apn']:
    #         val = getattr(self, attr)
    #         if val is not None:
    #             if attr == 'apn':
    #                 fields.append(f"{attr}={val!r}")
    #             else:
    #                 fields.append(f"{attr}='{val}'")
    #     # Add message count
    #     fields.append(f"messages={len(self.messages)}")
    #     return f"Subscriber({', '.join(fields)})"

    def add_avps(self, message: Message) -> Message:
        logger.debug(f"Subscriber AVPS: {self.avps}")
        for key, value in self.avps.items():
            if hasattr(message, key):
                setattr(message, key, value)
                logger.debug(f"Adding AVPS (subscriber): {key} = {value}")
        return message

    @property
    def subscription_id(self) -> List[SubscriptionId]:
        return self.get_subscription_id()

    def get_subscription_id(self) -> List[SubscriptionId]:
        """
        Create a SubscriptionId AVP for the subscriber.
        
        Returns:
            SubscriptionId: A new SubscriptionId AVP instance.
        """
        subscription_id: List[SubscriptionId] = []
        subscription_id.append(SubscriptionId(
            subscription_id_type=E_SUBSCRIPTION_ID_TYPE_END_USER_E164,
            subscription_id_data=self.msisdn
        ))
        if self.imsi:
            subscription_id.append(SubscriptionId(
                subscription_id_type=E_SUBSCRIPTION_ID_TYPE_END_USER_IMSI,
                subscription_id_data=self.imsi
            ))
        if self.sip_uri:
            subscription_id.append(SubscriptionId(
                subscription_id_type=E_SUBSCRIPTION_ID_TYPE_END_USER_SIP_URI,
                subscription_id_data=self.sip_uri
            ))
        if self.nai:
            subscription_id.append(SubscriptionId(
                subscription_id_type=E_SUBSCRIPTION_ID_TYPE_END_USER_NAI,
                subscription_id_data=self.nai
            ))
        if self.private_id:
            subscription_id.append(SubscriptionId(
                subscription_id_type=E_SUBSCRIPTION_ID_TYPE_END_USER_PRIVATE,
                subscription_id_data=self.private_id
            ))
        return subscription_id

    def add_message(self, message: DiameterMessage):
        self.messages.append(message)

    def add_session_id(self, app_id: int, session_id: str):
        with self._sessions_lock:
            if not app_id in self.sessions:
                self.sessions[app_id] = []
            if session_id not in self.sessions[app_id]:
                self.sessions[app_id].append(session_id)
    
    def get_session_id(self, app_id: int) -> Optional[str]:
        with self._sessions_lock:
            return self.sessions.get(app_id, []).copy()

    def to_dict(self) -> dict:
        subscriber_data = dict()
        subscriber_data['msisdn'] = self.msisdn
        if self.imsi:
            subscriber_data['imsi'] = self.imsi
        if self.sip_uri:
            subscriber_data['sip_uri'] = self.sip_uri
        if self.nai:
            subscriber_data['nai'] = self.nai
        if self.private_id:
            subscriber_data['private_id'] = self.private_id
        if self.imei:
            subscriber_data['imei'] = self.imei
        # if self.apn:
        #     subscriber_data['apn'] = self.apn.to_dict()
        subscriber_data['sessions'] = self.sessions
        # subscriber_data['message_count'] = len(self.messages)
        # subscriber_data['sample_messages'] = [msg.to_dict() for msg in self.messages[:3]]
        return subscriber_data

import uuid

@dataclass
class Subscribers:
    subscribers: Dict[str, Subscriber] = field(default_factory=dict, repr=True)
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8], repr=True)

    def values(self) -> List[Subscriber]:
        return list(self.subscribers.values())
    

    def get_subscribers(self) -> List[Subscriber]:
        return list(self.subscribers.values())

    def add_subscriber(self, subscriber: Subscriber):
        with self._lock:
            self.subscribers[subscriber.msisdn] = subscriber
    
    def get_subscriber_by_msisdn(self, msisdn: str) -> Optional[Subscriber]:
        with self._lock:
            return self.subscribers.get(msisdn)
    
    def get_subscriber_by_imsi(self, imsi: str) -> Optional[Subscriber]:
        with self._lock:
            for subscriber in self.subscribers.values():
                if subscriber.imsi == imsi:
                    return subscriber
            return None

    def create_subscriber(self, msisdn: str, imsi: str):
        with self._lock:
            subscriber = Subscriber(msisdn, imsi)
            self.add_subscriber(subscriber)
            return subscriber

    def to_dict(self) -> dict:
        with self._lock:
            subscribers_dict = dict()
            subscribers_dict['id'] = self.id
            subscribers_dict['subscribers'] = [subscriber.to_dict() for subscriber in self.subscribers.values()]
            return subscribers_dict
            # return [subscriber.to_dict() for subscriber in self.subscribers.values()]