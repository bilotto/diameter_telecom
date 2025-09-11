from ..subscriber import Subscriber, Subscribers
from .session import GxSession, RxSession, SySession, DiameterSession
from .session.sessions import Sessions
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import threading
import time
import logging
from .constants import *
from .parse_avp import *
from .message import DiameterMessage

logger = logging.getLogger(__name__)

CREATE_SESSION_MESSAGES = [CCR_I, AAR, SLR]

@dataclass
class SessionManager:
    sessions: Sessions = field(default_factory=Sessions)
    subscribers: Subscribers = field(default_factory=Subscribers)
    messages: List[DiameterMessage] = field(default_factory=list)

    def get_messages(self):
        return sorted(self.messages, key=lambda x: x.timestamp if x.timestamp else float('inf'))

    def stage_get_session(self, gv_stages: Dict) -> Optional[DiameterSession]:
        app_id = gv_stages['app_id']
        session_id = gv_stages['session_id']
        if session := self.sessions.get_session_by_id(app_id, session_id):
            gv_stages['session'] = session
        return session

    def stage_create_session(self, gv_stages: Dict) -> DiameterSession:
        dm: DiameterMessage = gv_stages['dm']
        app_id = dm.app_id
        session_id = dm.session_id
        subscriber = gv_stages.get('subscriber')

        framed_ip_address = None
        framed_ipv6_prefix = None
        called_station_id = None
        sgsn_mcc_mnc = None

        if hasattr(dm.message, 'framed_ip_address'):
            framed_ip_address = dm.message.framed_ip_address
        if hasattr(dm.message, 'framed_ipv6_prefix'):
            framed_ipv6_prefix = dm.message.framed_ipv6_prefix
        if hasattr(dm.message, 'called_station_id'):
            called_station_id = dm.message.called_station_id
        if hasattr(dm.message, 'sgsn_mcc_mnc'):
            sgsn_mcc_mnc = dm.message.sgsn_mcc_mnc
        
        if app_id == APP_3GPP_GX:
            session = GxSession(session_id=session_id, framed_ip_address=framed_ip_address, framed_ipv6_prefix=framed_ipv6_prefix, called_station_id=called_station_id, sgsn_mcc_mnc=sgsn_mcc_mnc, subscriber=subscriber)
        elif app_id == APP_3GPP_RX:
            session = RxSession(session_id=session_id, subscriber=subscriber)
        elif app_id == APP_3GPP_SY:
            session = SySession(session_id=session_id, subscriber=subscriber)
        else:
            raise ValueError(f"Unknown app_id: {app_id}")

        gv_stages['session'] = session

        if app_id == APP_3GPP_RX:
            self.stage_bind_rx_to_gx(gv_stages)
        
        self.sessions.add_session(app_id, session)
        return session

    def stage_get_subscriber(self, gv_stages: Dict) -> Optional[Subscriber]:
        if gv_stages.get('session') and gv_stages['session'].subscriber:
            subscriber = gv_stages['session'].subscriber
            gv_stages['subscriber'] = subscriber
            return subscriber
        return None

    def stage_identify_subscriber(self, gv_stages: Dict) -> Optional[Subscriber]:
        dm = gv_stages['dm']
        if hasattr(dm.message, 'subscription_id') and dm.message.subscription_id:
            msisdn, imsi, sip_uri, nai, private_id = parse_subscription_id(dm.message.subscription_id)
            subscriber = self.subscribers.get_subscriber_by_msisdn(msisdn) or self.subscribers.get_subscriber_by_imsi(imsi)
            if not subscriber:
                subscriber = Subscriber(msisdn=msisdn, imsi=imsi, sip_uri=sip_uri, nai=nai, private_id=private_id)
                self.subscribers.add_subscriber(subscriber)
                gv_stages['subscriber'] = subscriber
            return subscriber

        logger.warning(f"No subscriber found for message: {dm.name}")
        return None

    def stage_parse_request(self, gv_stages: Dict):
        dm = gv_stages['dm']
        session = self.stage_get_session(gv_stages)
        subscriber = self.stage_get_subscriber(gv_stages)
        if not subscriber:
            subscriber = self.stage_identify_subscriber(gv_stages)
        if not session and dm.name in CREATE_SESSION_MESSAGES:
            session = self.stage_create_session(gv_stages)
        return session, subscriber

    def stage_parse_response(self, gv_stages: Dict):
        dm = gv_stages['dm']
        session = self.stage_get_session(gv_stages)
        subscriber = self.stage_get_subscriber(gv_stages)
        if not session:
            logger.warning(f"No session found for response: {dm.name},{dm.session_id}")
        return session, subscriber

    def process_diameter_message(self, dm: DiameterMessage):
        gv_stages = dict()
        if not dm.timestamp:
            dm.timestamp = time.time()
        gv_stages['dm'] = dm
        gv_stages['session_id'] = dm.session_id
        gv_stages['app_id'] = dm.app_id
        print(f"Processing {dm.name} - {dm.session_id}")
        if dm.is_request:
            session, subscriber = self.stage_parse_request(gv_stages)
        else:
            session, subscriber = self.stage_parse_response(gv_stages)
        
        if session:
            session.add_message(dm)
        if subscriber:
            subscriber.add_message(dm)
            dm.subscriber = subscriber

        self.messages.append(dm)
        
    def stage_bind_rx_to_gx(self, gv_stages: Dict):
        dm: DiameterMessage = gv_stages['dm']
        rx_session = gv_stages['session']
        # if dm.app_id != APP_3GPP_RX:
        #     return

        if hasattr(dm.message, 'framed_ip_address') and dm.message.framed_ip_address:
            logger.debug(f"Trying to find GxSession by framed IP address: {dm.message.framed_ip_address}")
            gx_session = self.sessions.get_session_by_framed_ip(APP_3GPP_GX, dm.message.framed_ip_address)
            if gx_session:
                rx_session.gx_session_id = gx_session.session_id
                rx_session.subscriber = gx_session.subscriber
                logger.info(f"RxSession {rx_session.session_id} bound to GxSession {gx_session.session_id} via framed IP {dm.message.framed_ip_address}")
                return
        
        if hasattr(dm.message, 'subscription_id') and dm.message.subscription_id:
            logger.debug(f"Trying to find GxSession by MSISDN: {dm.message.subscription_id}")
            msisdn, imsi, _, _, _ = parse_subscription_id(dm.message.subscription_id)
            if msisdn:
                gx_session = self.sessions.get_session_by_msisdn(APP_3GPP_GX, msisdn)
                if gx_session:
                    rx_session.gx_session_id = gx_session.session_id
                    rx_session.subscriber = gx_session.subscriber
                    logger.info(f"RxSession {rx_session.session_id} bound to GxSession {gx_session.session_id} via MSISDN {msisdn}")
                    return
                    
        logger.warning(f"No GxSession found for RxSession {rx_session.session_id}")

    def send_request_with_session_management(self, diameter_message: DiameterMessage, send_request_func, timeout=10) -> DiameterMessage:
        self.process_diameter_message(diameter_message)
        logger.info(f"\n{diameter_message.dump()}")
        
        answer = send_request_func(diameter_message.message, timeout=timeout)
        diameter_message_answer = DiameterMessage(answer)
        
        self.process_diameter_message(diameter_message_answer)
        
        if diameter_message_answer.result_code != E_RESULT_CODE_DIAMETER_SUCCESS:
            logger.error(f"Answer with error: \n {diameter_message_answer}")
        logger.info(f"\n{diameter_message_answer.dump()}")
        
        return diameter_message_answer
