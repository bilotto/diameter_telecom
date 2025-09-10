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
    """Centralized session and subscriber management for Diameter applications.
    
    This class handles:
    - Session lifecycle management through the Sessions class
    - Subscriber management and identification
    - Message processing and timestamping
    - Request/response flow coordination
    """
    sessions: Sessions = field(default_factory=Sessions)
    subscribers: Subscribers = field(default_factory=Subscribers)
    messages: List[DiameterMessage] = field(default_factory=list)

    def get_messages(self):
        return sorted(self.messages, key=lambda x: x.timestamp if x.timestamp else float('inf'))

    # Note: Session and subscriber management methods are available directly through:
    # - self.sessions.* for session operations
    # - self.subscribers.* for subscriber operations

    def stage_get_session(self, dm: DiameterMessage) -> Optional[DiameterSession]:
        """Retrieve an existing session by app_id and session_id.
        
        Args:
            dm: DiameterMessage containing the session information
            
        Returns:
            Existing session if found, None otherwise
        """
        app_id = dm.app_id
        session_id = dm.session_id
        
        existing_session = self.sessions.get_session_by_id(app_id, session_id)
        if existing_session:
            existing_session.add_message(dm)
            return existing_session
        
        return None

    def stage_create_session(self, dm: DiameterMessage, subscriber: Optional[Subscriber] = None) -> DiameterSession:
        """Create a new session for the given Diameter message.
        
        Args:
            dm: DiameterMessage containing the session information
            
        Returns:
            The newly created session
            
        Raises:
            ValueError: If app_id is not supported
        """
        app_id = dm.app_id
        session_id = dm.session_id

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
        
        # Create new session
        if app_id == APP_3GPP_GX:
            session = GxSession(session_id=session_id, framed_ip_address=framed_ip_address, framed_ipv6_prefix=framed_ipv6_prefix, called_station_id=called_station_id, sgsn_mcc_mnc=sgsn_mcc_mnc, subscriber=subscriber)
        elif app_id == APP_3GPP_RX:
            session = RxSession(session_id=session_id, subscriber=subscriber)
            # Bind RxSession to GxSession if this is an Rx request
            self.stage_bind_rx_to_gx(session, dm)
        elif app_id == APP_3GPP_SY:
            session = SySession(session_id=session_id, subscriber=subscriber)
        else:
            raise ValueError(f"Unknown app_id: {app_id}")
        
        self.sessions.add_session(app_id, session)
        session.add_message(dm)
        return session

    def stage_identify_subscriber(self, dm: DiameterMessage, session: Optional[DiameterSession] = None) -> Optional[Subscriber]:
        if session:
            return session.subscriber

        if hasattr(dm.message, 'subscription_id') and dm.message.subscription_id:
            msisdn, imsi, sip_uri, nai, private_id = parse_subscription_id(dm.message.subscription_id)
            subscriber = self.subscribers.get_subscriber_by_msisdn(msisdn) or self.subscribers.get_subscriber_by_imsi(imsi)
            if not subscriber:
                subscriber = Subscriber(msisdn=msisdn, imsi=imsi, sip_uri=sip_uri, nai=nai, private_id=private_id)
                self.subscribers.add_subscriber(subscriber)
            return subscriber

        logger.warning(f"No subscriber found for message: {dm.name}")
        return None

    def stage_parse_request(self, dm: DiameterMessage):
        session = self.stage_get_session(dm)
        subscriber = self.stage_identify_subscriber(dm, session)

        if subscriber and not dm.subscriber:
            dm.subscriber = subscriber
        
        # If no existing session found, create a new one
        if not session and dm.name in CREATE_SESSION_MESSAGES:
            session = self.stage_create_session(dm, subscriber)
        
        # Associate subscriber with session if found
        if subscriber and session and not session.subscriber:
            session.subscriber = subscriber
        
    def stage_bind_rx_to_gx(self, rx_session: RxSession, dm: DiameterMessage):
        """Bind RxSession to existing GxSession based on framed IP address or other identifiers"""
        if dm.app_id != APP_3GPP_RX:
            return

        # Try to find GxSession by framed IP address first
        if hasattr(dm.message, 'framed_ip_address') and dm.message.framed_ip_address:
            logger.debug(f"Trying to find GxSession by framed IP address: {dm.message.framed_ip_address}")
            gx_session = self.sessions.get_session_by_framed_ip(APP_3GPP_GX, dm.message.framed_ip_address)
            if gx_session:
                rx_session.gx_session_id = gx_session.session_id
                rx_session.subscriber = gx_session.subscriber
                logger.info(f"RxSession {rx_session.session_id} bound to GxSession {gx_session.session_id} via framed IP {dm.message.framed_ip_address}")
                return
        
        # Try to find GxSession by MSISDN if available
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
                    
        # If no GxSession found, log a warning
        logger.warning(f"No GxSession found for RxSession {rx_session.session_id}")

    def stage_parse_response(self, dm: DiameterMessage):
        app_id = dm.app_id
        session_id = dm.session_id
        session = self.sessions.get_session_by_id(app_id, session_id)
        if not session:
            return
        session.add_message(dm)

    def process_diameter_message(self, dm: DiameterMessage):
        """Main entry point for processing Diameter messages"""
        # Set timestamp if not already set
        if not dm.timestamp:
            dm.timestamp = time.time()
            
        self.messages.append(dm)
        if dm.is_request:
            self.stage_parse_request(dm)
        else:
            self.stage_parse_response(dm)

    def send_request_with_session_management(self, diameter_message: DiameterMessage, send_request_func, timeout=10) -> DiameterMessage:
        """Process request message, send it, and process response with full session management"""
        # Process the request
        self.process_diameter_message(diameter_message)
        logger.info(f"\n{diameter_message.dump()}")
        
        # Send the request
        answer = send_request_func(diameter_message.message, timeout=timeout)
        diameter_message_answer = DiameterMessage(answer)
        
        # Process the response
        self.process_diameter_message(diameter_message_answer)
        
        if diameter_message_answer.result_code != E_RESULT_CODE_DIAMETER_SUCCESS:
            logger.error(f"Answer with error: \n {diameter_message_answer}")
        logger.info(f"\n{diameter_message_answer.dump()}")
        
        return diameter_message_answer
  