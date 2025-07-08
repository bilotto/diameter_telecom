from dataclasses import dataclass
from typing import List
from diameter.message.avp.grouped import SubscriptionId
from .diameter.constants import *
from .apn import APN

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
    """
    msisdn: str
    imsi: str
    sip_uri: str = None
    nai: str = None
    private_id: str = None
    imei: str = None
    apn: APN = None

    def __post_init__(self):
        """
        Post-initialization hook to ensure proper type conversion of all fields.
        
        Converts all non-None attributes to strings to ensure consistent type handling.
        """
        for attr in ['msisdn', 'imsi', 'sip_uri', 'nai', 'private_id', 'imei']:
            val = getattr(self, attr)
            if val is not None:
                setattr(self, attr, str(val))

    def subscription_id(self) -> List[SubscriptionId]:
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
