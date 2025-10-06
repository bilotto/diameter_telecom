from typing import List, Dict, Optional
from dataclasses import dataclass, field
from .subscriber import Subscriber, Subscribers
from .apn import APN

@dataclass
class Carrier:
    name: str
    mcc_mnc: List[str]
    country_code: str
    apns: Dict[str, APN] = field(default_factory=dict)
    subscribers: Subscribers = field(default_factory=Subscribers)
    apn_list: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.mcc_mnc, list):
            self.mcc_mnc = list(self.mcc_mnc)
        else:
            self.mcc_mnc = self.mcc_mnc
        self.country_code = str(self.country_code)

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

    # def create_subscriber(self, msisdn: str, imsi: str = None) -> Subscriber:
    #     subscriber = Subscriber(msisdn=msisdn, imsi=imsi)
    #     self.add_subscriber(subscriber)
    #     return subscriber
