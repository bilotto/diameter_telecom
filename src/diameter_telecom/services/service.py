# from .ip_queue import APN
from ..diameter.message import DiameterMessage
from ..entities_3gpp import PCEF, OCS, AF
from ..diameter.constants import *
from ..diameter.session import GxSession, SySession
from ..subscriber import Subscriber
# import logging
# logger = logging.getLogger(__name__)
import time
from ..apn import *
from ..carrier import Carrier
from dataclasses import dataclass
from ..csv_file import CsvFile, write_to_csv


@dataclass
class Service:
    pcef: PCEF
    ocs: OCS = None
    af: AF = None
    diameter_config: dict = None
    carrier: Carrier = None
    csv_file: CsvFile = None

    def __post_init__(self):
        if self.diameter_config is None:
            self.diameter_config = {}
            self.diameter_config[APP_3GPP_GX] = {}
            if self.ocs:
                self.diameter_config[APP_3GPP_SY] = {}
            if self.af:
                self.diameter_config[APP_3GPP_RX] = {}

    @property
    def gx_app(self):
        return self.pcef.gx_app

    @property
    def sy_app(self):
        if self.ocs:
            return self.ocs.sy_app
    @property
    def rx_app(self):
        if self.af:
            return self.af.rx_app
        
    def set_host_and_realm(self, diameter_message: DiameterMessage):
        if diameter_message.app_id == APP_3GPP_GX:
            diameter_message.message.origin_host = self.pcef.origin_host.encode()
            diameter_message.message.origin_realm = (self.diameter_config[APP_3GPP_GX].get('origin_realm') or self.pcef.realm_name).encode()
            diameter_message.message.destination_realm = (self.diameter_config[APP_3GPP_GX].get('destination_realm') or self.pcef.realm_name).encode()
            if diameter_message.message.destination_host:
                diameter_message.message.destination_host = (self.diameter_config[APP_3GPP_GX].get('destination_host') or self.pcef.realm_name).encode()
        elif diameter_message.app_id == APP_3GPP_RX:
            diameter_message.message.origin_host = self.af.origin_host.encode()
            diameter_message.message.origin_realm = (self.diameter_config[APP_3GPP_RX].get('origin_realm') or self.af.realm_name).encode()
            diameter_message.message.destination_realm = (self.diameter_config[APP_3GPP_RX].get('destination_realm') or self.af.realm_name).encode()
            if diameter_message.message.destination_host:
                diameter_message.message.destination_host = (self.diameter_config[APP_3GPP_RX].get('destination_host') or self.af.realm_name).encode()
        elif diameter_message.app_id == APP_3GPP_SY:
            diameter_message.message.origin_host = self.ocs.origin_host.encode()
            diameter_message.message.origin_realm = (self.diameter_config[APP_3GPP_SY].get('origin_realm') or self.ocs.realm_name).encode()
            diameter_message.message.destination_realm = (self.diameter_config[APP_3GPP_SY].get('destination_realm') or self.ocs.realm_name).encode()
            if diameter_message.message.destination_host:
                diameter_message.message.destination_host = (self.diameter_config[APP_3GPP_SY].get('destination_host') or self.ocs.realm_name).encode()
        else:
            raise ValueError(f"Invalid app_id: {diameter_message.app_id}. Maybe missing to set the header?")
        return diameter_message
        
    def start(self):
        if not self.gx_app.node._started:
            self.gx_app.node.start()
        if self.sy_app:
            if not self.sy_app.node._started:
                self.sy_app.node.start()
        if self.rx_app:
            if not self.rx_app.node._started:
                self.rx_app.node.start()

    def stop(self):
        if self.gx_app.node._started:
            self.gx_app.node.stop()
        if self.sy_app:
            if self.sy_app.node._started:
                self.sy_app.node.stop()
        if self.rx_app:
            if self.rx_app.node._started:
                self.rx_app.node.stop()


    def wait_for_ready(self):
        self.gx_app.wait_for_ready()
        if self.sy_app:
            self.sy_app.wait_for_ready()
        if self.rx_app:
            self.rx_app.wait_for_ready()