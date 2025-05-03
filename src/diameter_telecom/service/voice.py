from .ip_queue import APN
from ..diameter_message import DiameterMessage
from ..app import GxApplication, RxApplication
from diameter.message.constants import APP_3GPP_GX, APP_3GPP_RX

class VoiceService:
    def __init__(self, gx_app: GxApplication, rx_app: RxApplication):
        self.gx_app: GxApplication = gx_app
        self.rx_app: RxApplication = rx_app

    def start(self):
        if not self.gx_app.node._started:
            self.gx_app.node.start()
        if not self.rx_app.node._started:
            self.rx_app.node.start()
        self.gx_app.wait_for_ready()
        self.rx_app.wait_for_ready()

    def stop(self):
        if self.gx_app.node._started:
            self.gx_app.node.stop()
        if self.rx_app.node._started:
            self.rx_app.node.stop()

    def send_request(self, request: DiameterMessage, timeout=5):
        if request.app_id == APP_3GPP_GX:
            answer = self.gx_app.send_request_custom(request, timeout)
        elif request.app_id == APP_3GPP_RX:
            answer = self.rx_app.send_request_custom(request, timeout)
        return answer

