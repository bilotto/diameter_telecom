from typing import List, Dict, Optional
from dataclasses import dataclass, field
from .subscriber import Subscriber
from .apn import APN

@dataclass
class Carrier:
    """
    Represents a telecommunications carrier with subscriber management capabilities.
    
    This class manages carrier information and its associated subscribers. It provides
    functionality to add and manage subscribers within the carrier's network.
    
    Attributes:
        name (str): The name of the carrier/operator
        mcc_mnc (str): Mobile Country Code and Mobile Network Code, uniquely identifying
                      the carrier in the global mobile network
        country_code (str): The country code where the carrier operates
        subscribers (Dict[str, Subscriber]): Dictionary of subscribers indexed by their MSISDN
    """
    name: str
    mcc_mnc: str
    country_code: str
    subscribers: Dict[str, Subscriber] = field(default_factory=dict)
    apns: Dict[str, APN] = field(default_factory=dict)

    def __post_init__(self):
        """
        Post-initialization hook to ensure proper type conversion of critical fields.
        
        Converts mcc_mnc and country_code to strings to ensure consistent type handling.
        """
        self.mcc_mnc = str(self.mcc_mnc)
        self.country_code = str(self.country_code)

    def add_subscriber(self, subscriber: Subscriber) -> Subscriber:
        """
        Add a subscriber to the carrier's subscriber list.
        
        Args:
            subscriber (Subscriber): The subscriber object to add to the carrier
            
        Returns:
            Subscriber: The added subscriber object
            
        Raises:
            ValueError: If the provided subscriber is not an instance of Subscriber class
        """
        if not isinstance(subscriber, Subscriber):
            raise ValueError("subscriber must be an instance of Subscriber")
        self.subscribers[subscriber.msisdn] = subscriber
        return self.subscribers[subscriber.msisdn]
    
    def add_apn(self, apn: APN) -> APN:
        self.apns[apn.apn] = apn
        return self.apns[apn.apn]
