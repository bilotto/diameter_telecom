from dataclasses import dataclass

@dataclass
class Subscriber:
    msisdn: str
    imsi: str
    imei: str = None

    def __post_init__(self):
        self.msisdn = str(self.msisdn)
        self.imsi = str(self.imsi)