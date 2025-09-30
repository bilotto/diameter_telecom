# from .ip_queue import APN
from ..diameter.message import DiameterMessage, create_message
from ..entities_3gpp import PCEF, OCS, AF
from ..entities_3gpp.ip_queue import IpQueue
from ..diameter.constants import *
from ..diameter.session import GxSession, SySession
from ..subscriber import Subscriber
import logging
logger = logging.getLogger(__name__)
import time
from ..apn import *
from ..carrier import Carrier
from dataclasses import dataclass, field
from ..csv_file import CsvFile, write_to_csv
from ..diameter.session_manager import SessionManager
from .diameter_config import DiameterConfig, create_diameter_config_from_entities
import warnings
from ..apn import IpQueue, bytes_to_ip, ip_to_bytes

@dataclass
class Service:
    pcef: PCEF
    ocs: OCS = None
    af: AF = None
    diameter_config: object = None
    carrier: Carrier = None
    csv_file: CsvFile = None
    ip_queue: IpQueue = None
    session_manager: SessionManager = None
    
    def __post_init__(self):
        logger.info(f"Initializing Service with PCEF: {self.pcef.origin_host}")
        if self.diameter_config is None:
            # Auto-create configuration from entities
            self.diameter_config = create_diameter_config_from_entities(self.pcef, self.ocs, self.af)
            logger.info(f"Auto-created DiameterConfig from entities")
        else:
            # Accept dict or DiameterConfig for backward compatibility
            if isinstance(self.diameter_config, DiameterConfig):
                logger.info(f"Using provided DiameterConfig object")
            elif isinstance(self.diameter_config, dict):
                warnings.warn(
                    "Passing raw dict for diameter_config is deprecated; it will continue to work but may be removed in a future release.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                self.diameter_config = DiameterConfig(self.diameter_config)
                logger.info(f"Wrapped legacy dict into DiameterConfig")
            else:
                # Last resort: try to coerce unknown types via dict()
                try:
                    self.diameter_config = DiameterConfig(dict(self.diameter_config))
                    logger.info(f"Coerced provided config into DiameterConfig via dict()")
                except Exception:
                    logger.warning(f"Unsupported diameter_config type; falling back to empty config")
                    self.diameter_config = DiameterConfig()
        
        # Convert DiameterConfig to internal format for compatibility
        self._internal_config = self.diameter_config.get_config()
        logger.debug(f"Service diameter configuration: {list(self._internal_config.keys())}")
        self.set_session_manager(SessionManager())

    def set_ip_queue(self, ip_range_cidr: str):
        self.ip_queue = IpQueue(ip_range_cidr)

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

    def set_session_manager(self, session_manager: SessionManager = None):
        session_manager = session_manager if session_manager else SessionManager()
        logger.info(f"Setting session manager on service applications")
        self.gx_app.set_session_manager(session_manager)
        logger.debug(f"Session manager set on Gx application")
        if self.ocs:
            self.sy_app.set_session_manager(session_manager)
            logger.debug(f"Session manager set on Sy application")
        if self.af:
            self.rx_app.set_session_manager(session_manager)
            logger.debug(f"Session manager set on Rx application")
        self.session_manager = session_manager
        
    def set_host_and_realm(self, diameter_message: DiameterMessage):
        if diameter_message.app_id == APP_3GPP_GX:
            diameter_message.message.origin_host = self.pcef.origin_host.encode()
            diameter_message.message.origin_realm = (self._internal_config[APP_3GPP_GX].get('origin_realm') or self.pcef.realm_name).encode()
            diameter_message.message.destination_realm = (self._internal_config[APP_3GPP_GX].get('destination_realm') or self.pcef.realm_name).encode()
            if diameter_message.message.destination_host:
                diameter_message.message.destination_host = (self._internal_config[APP_3GPP_GX].get('destination_host') or self.pcef.realm_name).encode()
        elif diameter_message.app_id == APP_3GPP_RX:
            diameter_message.message.origin_host = self.af.origin_host.encode()
            diameter_message.message.origin_realm = (self._internal_config[APP_3GPP_RX].get('origin_realm') or self.af.realm_name).encode()
            diameter_message.message.destination_realm = (self._internal_config[APP_3GPP_RX].get('destination_realm') or self.af.realm_name).encode()
            if diameter_message.message.destination_host:
                diameter_message.message.destination_host = (self._internal_config[APP_3GPP_RX].get('destination_host') or self.af.realm_name).encode()
        elif diameter_message.app_id == APP_3GPP_SY:
            diameter_message.message.origin_host = self.ocs.origin_host.encode()
            diameter_message.message.origin_realm = (self._internal_config[APP_3GPP_SY].get('origin_realm') or self.ocs.realm_name).encode()
            diameter_message.message.destination_realm = (self._internal_config[APP_3GPP_SY].get('destination_realm') or self.ocs.realm_name).encode()
            if diameter_message.message.destination_host:
                diameter_message.message.destination_host = (self._internal_config[APP_3GPP_SY].get('destination_host') or self.ocs.realm_name).encode()
        else:
            raise ValueError(f"Invalid app_id: {diameter_message.app_id}. Maybe missing to set the header?")
        return diameter_message
        
    def start(self):
        logger.info(f"Starting Service applications...")
        if not self.gx_app.node._started:
            logger.debug(f"Starting Gx application node")
            self.gx_app.node.start()
        if self.sy_app:
            if not self.sy_app.node._started:
                logger.debug(f"Starting Sy application node")
                self.sy_app.node.start()
        if self.rx_app:
            if not self.rx_app.node._started:
                logger.debug(f"Starting Rx application node")
                self.rx_app.node.start()
        logger.info(f"Service applications started successfully")

    def stop(self):
        logger.info(f"Stopping Service applications...")
        if self.gx_app.node._started:
            logger.debug(f"Stopping Gx application node")
            self.gx_app.node.stop()
        if self.sy_app:
            if self.sy_app.node._started:
                logger.debug(f"Stopping Sy application node")
                self.sy_app.node.stop()
        if self.rx_app:
            if self.rx_app.node._started:
                logger.debug(f"Stopping Rx application node")
                self.rx_app.node.stop()
        logger.info(f"Service applications stopped successfully")


    def wait_for_ready(self):
        logger.info(f"Waiting for Service applications to be ready...")
        self.gx_app.wait_for_ready()
        logger.debug(f"Gx application ready")
        if self.sy_app:
            self.sy_app.wait_for_ready()
            logger.debug(f"Sy application ready")
        if self.rx_app:
            self.rx_app.wait_for_ready()
            logger.debug(f"Rx application ready")
        logger.info(f"All Service applications ready")

    def send_request(self, request: DiameterMessage, timeout=5) -> DiameterMessage:
        if not isinstance(request, DiameterMessage):
            raise TypeError("request must be an instance of DiameterMessage")
        request.timestamp = time.time()
        session_id = request.session_id        
        request = self.set_host_and_realm(request)
        if request.app_id == APP_3GPP_GX:
            answer: DiameterMessage = self.gx_app.send_request_custom(request, timeout)
        elif request.app_id == APP_3GPP_RX and self.af:
            answer: DiameterMessage = self.rx_app.send_request_custom(request, timeout)
        elif request.app_id == APP_3GPP_SY and self.ocs:
            answer: DiameterMessage = self.sy_app.send_request_custom(request, timeout)
        else:
            raise ValueError(f"DataService cannot handle app_id: {request.app_id}")
        return answer

    def create_gx_session(self, subscriber: Subscriber) -> GxSession:
        session_id = self.gx_app.node.session_generator.next_id()
        gx_session = GxSession(session_id=session_id, subscriber=subscriber)
        gx_session.framed_ip_address = self.ip_queue.get_ip()
        return gx_session


    def start_gx_session(self, gx_session: GxSession):
        ccr_i = create_message(CCR_I)
        ccr_i.header.application_id = APP_3GPP_GX
        ccr_i.auth_application_id = APP_3GPP_GX
        ccr_i.session_id = gx_session.session_id
        ccr_i.subscription_id = gx_session.subscriber.subscription_id
        ccr_i.service_context_id = "test"
        ccr_i.origin_state_id = 0
        ccr_i.rat_type = gx_session.rat_type
        ccr_i.framed_ip_address = ip_to_bytes(gx_session.framed_ip_address)
        ccr_i.called_station_id = gx_session.called_station_id
        ccr_i.sgsn_mcc_mnc = gx_session.sgsn_mcc_mnc
            
        return self.send_request(DiameterMessage(ccr_i))

