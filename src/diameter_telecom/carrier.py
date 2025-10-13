from typing import List, Dict, Optional
from dataclasses import dataclass, field
from .subscriber import Subscriber, Subscribers
from .apn import APN
from .subscriber_generator import SubscriberGenerator

@dataclass
class Carrier:
    name: str
    mcc_mnc: List[str]
    country_code: str
    apns: Dict[str, APN] = field(default_factory=dict)
    subscribers: Subscribers = field(default_factory=Subscribers)
    apn_list: List[str] = field(default_factory=list)
    msisdn_length: int = 13
    imsi_length: int = 15

    def __post_init__(self):
        if not isinstance(self.mcc_mnc, list):
            self.mcc_mnc = list(self.mcc_mnc)
        else:
            self.mcc_mnc = self.mcc_mnc
        self.country_code = str(self.country_code)
        
        # Initialize subscriber generator
        # Use the first MCC/MNC from the list as the primary one
        primary_mcc_mnc = self.mcc_mnc[0] if self.mcc_mnc else "00000"
        self.subscriber_generator = SubscriberGenerator(
            carrier_name=self.name,
            mcc_mnc=primary_mcc_mnc,
            country_code=self.country_code,
            msisdn_length=self.msisdn_length,
            imsi_length=self.imsi_length
        )

    # def add_subscriber(self, subscriber: Subscriber) -> Subscriber:
    #     if not isinstance(subscriber, Subscriber):
    #         raise ValueError("subscriber must be an instance of Subscriber")
    #     self.subscribers.add_subscriber(subscriber)
    #     return self.subscribers.get_subscriber_by_msisdn(subscriber.msisdn)
    
    # def add_apn(self, apn: APN) -> APN:
    #     self.apns[apn.apn] = apn
    #     return self.apns[apn.apn]
    
    # def get_apn(self, apn_name: str) -> Optional[APN]:
    #     return self.apns.get(apn_name)
    
    # def create_apn(self, apn_name: str, ip_pool_cidr: str) -> APN:
    #     apn = APN(apn=apn_name, ip_pool_cidr=ip_pool_cidr)
    #     self.add_apn(apn)
    #     return apn

    def create_subscriber(self, msisdn: str = None, imsi: str = None, **kwargs) -> Subscriber:
        """Create a new subscriber with generated or provided identifiers.
        
        Args:
            msisdn: Optional MSISDN. If not provided, will be generated.
            imsi: Optional IMSI. If not provided, will be generated.
            **kwargs: Additional subscriber attributes (sip_uri, nai, etc.)
        
        Returns:
            A new Subscriber instance
        """
        if msisdn is None or imsi is None:
            generated_msisdn, generated_imsi = self.subscriber_generator.next_subscriber()
            msisdn = msisdn or generated_msisdn
            imsi = imsi or generated_imsi
        
        subscriber = Subscriber(
            msisdn=msisdn,
            imsi=imsi,
            carrier_name=self.name,
            **kwargs
        )
        
        self.subscribers.add_subscriber(subscriber)
        return subscriber
    
    def create_subscribers_batch(self, count: int, **kwargs) -> List[Subscriber]:
        """Create multiple subscribers at once.
        
        Args:
            count: Number of subscribers to create
            **kwargs: Additional subscriber attributes
        
        Returns:
            List of new Subscriber instances
        """
        subscribers = []
        for _ in range(count):
            subscriber = self.create_subscriber(**kwargs)
            subscribers.append(subscriber)
        return subscribers
    
    def get_subscriber_generator_stats(self) -> dict:
        """Get statistics about the subscriber generator.
        
        Returns:
            Dictionary with generator statistics
        """
        return self.subscriber_generator.get_stats()
