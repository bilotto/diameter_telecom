from typing import List, Dict, Optional
from dataclasses import dataclass, field
from .subscriber import Subscriber

@dataclass
class Carrier:
    name: str
    mcc_mnc: str
    country_code: str
    subscribers: Dict[str, Subscriber] = field(default_factory=dict)

    def __post_init__(self):
        self.mcc_mnc = str(self.mcc_mnc)
        self.country_code = str(self.country_code)

    def add_subscriber(self, subscriber: Subscriber):
        if not isinstance(subscriber, Subscriber):
            raise ValueError("subscriber must be an instance of Subscriber")
        self.subscribers[subscriber.msisdn] = subscriber
        return self.subscribers[subscriber.msisdn]