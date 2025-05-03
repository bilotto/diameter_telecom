from dataclasses import dataclass

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
        imei (str, optional): International Mobile Equipment Identity. A unique
                             identifier for the subscriber's mobile device.
    """
    msisdn: str
    imsi: str
    imei: str = None

    def __post_init__(self):
        """
        Post-initialization hook to ensure proper type conversion of critical fields.
        
        Converts msisdn and imsi to strings to ensure consistent type handling.
        """
        self.msisdn = str(self.msisdn)
        self.imsi = str(self.imsi)