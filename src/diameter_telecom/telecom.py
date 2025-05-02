from typing import List, Dict, Optional
from dataclasses import dataclass, field
from .subscriber import Subscriber
from .service import DataService
from .service.ip_queue import APN

@dataclass
class Carrier:
    name: str
    mcc_mnc: str
    country_code: str
    subscribers: Dict[str, Subscriber] = field(default_factory=dict)
    apns: Dict[str, APN] = field(default_factory=dict)
    data_service: Optional[DataService] = field(default=None)

    def __post_init__(self):
        self.mcc_mnc = str(self.mcc_mnc)
        self.country_code = str(self.country_code)

    def add_subscriber(self, subscriber: Subscriber):
        if not isinstance(subscriber, Subscriber):
            raise ValueError("subscriber must be an instance of Subscriber")
        self.subscribers[subscriber.msisdn] = subscriber
        return self.subscribers[subscriber.msisdn]

    def set_data_service(self, data_service: DataService):
        if not isinstance(data_service, DataService):
            raise ValueError("data_service must be an instance of DataService")
        self.data_service = data_service
        return self.data_service
    
    def create_apn(self, apn_name, ip_pool_cidr):
        apn = APN(apn_name, ip_pool_cidr)
        self.apns[apn_name] = apn
        return apn