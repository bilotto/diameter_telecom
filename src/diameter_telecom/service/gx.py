# from diameter.message.constants import *
# from diameter.message.commands import *
# from diameter.message.avp.grouped import *
from .ip_queue import APN
from ..diameter_message import DiameterMessage
from ..app import GxApplication

class GxService:
    gx_app: GxApplication
    apn: APN
    gx_config: dict
    def __init__(self,
                 gx_app: GxApplication,
                 gx_config: dict = None,
                 apn: APN = None,
                 ):
        if not isinstance(gx_app, GxApplication):
            raise ValueError("gx_app must be an instance of GxApplication")
        if apn and not isinstance(apn, APN):
            raise ValueError("apn must be an instance of APN")
        self.gx_app = gx_app
        self.gx_config = gx_config
        self.apn = apn

    @property
    def app(self):
        return self.gx_app
    
    def __getattribute__(self, name):
        if self.gx_config and name in self.gx_config:
            return self.gx_config[name]
        return super().__getattribute__(name)
    
    
    def send_gx_request(self, request: DiameterMessage, timeout=5):
        if not isinstance(request, DiameterMessage):
            raise ValueError("request must be an instance of Message")
        if self.origin_realm:
            request.origin_realm = self.origin_realm.encode()
        if self.origin_host:
            request.origin_host = self.origin_host.encode()
        if self.destination_realm:
            request.destination_realm = self.destination_realm.encode()
        if self.destination_host:
            request.destination_host = self.destination_host.encode()
        return self.gx_app.send_request_custom(request, timeout)
        
    # def create_gx_session(self, subscriber: Subscriber, session_id=None) -> GxSession:
    #     if not session_id:
    #         # gx_session_id = self.gx_app.node.session_generator.next_id()
    #         timestamp = int(time.time())
    #         gx_session_id = f"GxSession_{timestamp}_{subscriber.msisdn}_{subscriber.imsi}"
    #     else:
    #         gx_session_id = session_id
    #     framed_ip_address = self.apn.ip_queue.get_ip()
    #     apn = self.apn.value
    #     gx_session = self.gx_app.sessions.create_session(subscriber, gx_session_id, framed_ip_address, apn)
    #     return gx_session
    