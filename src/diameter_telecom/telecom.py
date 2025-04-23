from typing import List, Dict
from .subscriber import Subscriber
from .service import DataService
from .service.ip_queue import APN

class Carrier:
    name: str
    mcc_mnc: str
    country_code: str
    subscribers: Dict[str, Subscriber]
    data_service: DataService


    def __init__(self, 
                 name,
                 mcc_mnc: str,
                 country_code: str,
                 ):
        self.name = name
        self.mcc_mnc = str(mcc_mnc)
        self.country_code = str(country_code)
        self.subscribers = {}
        self.apns = {}
        self.data_service = None

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