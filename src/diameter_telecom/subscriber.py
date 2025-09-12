from dataclasses import dataclass, field
from typing import List, Dict, Optional
from diameter.message.avp.grouped import SubscriptionId
from .diameter.constants import *
from .apn import APN
from .diameter.message import DiameterMessage

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
    apn: APN = field(default=None, repr=False)
    messages: List[DiameterMessage] = field(default_factory=list, repr=False)
    session_ids: Dict[int, List[str]] = field(default_factory=dict, repr=True)

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
        """
        Add a Diameter message to the subscriber's message history.
        
        Args:
            message: The DiameterMessage to add to the subscriber's history
        """
        self.messages.append(message)

    def add_session_id(self, app_id: int, session_id: str):
        # self.session_ids[app_id] = session_id
        if not app_id in self.session_ids:
            self.session_ids[app_id] = []
        self.session_ids[app_id].append(session_id)
    
    def get_session_id(self, app_id: int) -> Optional[str]:
        return self.session_ids.get(app_id, [])

    def to_json(self) -> dict:
        """
        Convert Subscriber to JSON-serializable dictionary.
        
        Returns:
            dict: JSON-serializable representation of the subscriber
        """
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
        if self.apn:
            subscriber_data['apn'] = self.apn.to_json()
        subscriber_data['session_ids'] = self.session_ids
        # subscriber_data['message_count'] = len(self.messages)
        # subscriber_data['sample_messages'] = [msg.to_json() for msg in self.messages[:3]]
        return subscriber_data

@dataclass
class Subscribers:
    subscribers: Dict[str, Subscriber] = field(default_factory=dict)

    def add_subscriber(self, subscriber: Subscriber):
        self.subscribers[subscriber.msisdn] = subscriber
    
    def get_subscriber_by_msisdn(self, msisdn: str) -> Optional[Subscriber]:
        return self.subscribers.get(msisdn)
    
    def get_subscriber_by_imsi(self, imsi: str) -> Optional[Subscriber]:
        for subscriber in self.subscribers.values():
            if subscriber.imsi == imsi:
                return subscriber
        return None
    
    # def get_subscribers_with_messages(self) -> List[Subscriber]:
    #     """
    #     Get all subscribers that have associated messages.
        
    #     Returns:
    #         List of Subscriber objects that have messages
    #     """
    #     return [subscriber for subscriber in self.subscribers.values() if subscriber.messages]
    
    # def get_total_messages(self) -> int:
    #     """
    #     Get the total number of messages across all subscribers.
        
    #     Returns:
    #         Total count of messages for all subscribers
    #     """
    #     return sum(len(subscriber.messages) for subscriber in self.subscribers.values())

    def to_json(self) -> dict:
        return {msisdn: subscriber.to_json() for msisdn, subscriber in self.subscribers.items()}