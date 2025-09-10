from ..subscriber import Subscriber, Subscribers
from .session import GxSession, RxSession, SySession, DiameterSession
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import threading
import time
import logging
from .constants import *
from .parse_avp import *
from .message import DiameterMessage

logger = logging.getLogger(__name__)

@dataclass
class SessionManager:
    sessions: Dict[int, Dict[str, DiameterSession]] = field(default_factory=dict)
    subscribers: Subscribers = field(default_factory=Subscribers)
    messages: List[DiameterMessage] = field(default_factory=list)
    # Indexing for fast lookups
    sessions_by_framed_ip: Dict[int, Dict[str, str]] = field(default_factory=dict)
    sessions_by_framed_ipv6: Dict[int, Dict[str, str]] = field(default_factory=dict)
    sessions_by_msisdn: Dict[int, Dict[str, str]] = field(default_factory=dict)

    def __post_init__(self):
        # Ensure the main session dicts for each app_id are present
        self.sessions.setdefault(APP_3GPP_GX, dict())
        self.sessions.setdefault(APP_3GPP_RX, dict())
        self.sessions.setdefault(APP_3GPP_SY, dict())
        
        # Initialize indexing dictionaries
        self.sessions_by_framed_ip.setdefault(APP_3GPP_GX, dict())
        self.sessions_by_framed_ipv6.setdefault(APP_3GPP_GX, dict())
        self.sessions_by_msisdn.setdefault(APP_3GPP_GX, dict())

    def get_messages(self):
        return sorted(self.messages, key=lambda x: x.timestamp if x.timestamp else float('inf'))

    # Session lookup methods
    def get_session_by_id(self, app_id: int, session_id: str) -> Optional[DiameterSession]:
        """Get session by application ID and session ID"""
        return self.sessions.get(app_id, {}).get(session_id)
    
    def get_session_by_framed_ip(self, app_id: int, ip_address: str) -> Optional[DiameterSession]:
        """Get session by framed IP address"""
        session_id = self.sessions_by_framed_ip.get(app_id, {}).get(ip_address)
        if session_id:
            return self.get_session_by_id(app_id, session_id)
        return None
    
    def get_session_by_framed_ipv6(self, app_id: int, ipv6_prefix: str) -> Optional[DiameterSession]:
        """Get session by framed IPv6 prefix"""
        session_id = self.sessions_by_framed_ipv6.get(app_id, {}).get(ipv6_prefix)
        if session_id:
            return self.get_session_by_id(app_id, session_id)
        return None
    
    def get_session_by_msisdn(self, app_id: int, msisdn: str) -> Optional[DiameterSession]:
        """Get session by MSISDN"""
        session_id = self.sessions_by_msisdn.get(app_id, {}).get(msisdn)
        if session_id:
            return self.get_session_by_id(app_id, session_id)
        return None

    # Subscriber management methods
    def get_subscriber_by_msisdn(self, msisdn: str) -> Optional[Subscriber]:
        """Get subscriber by MSISDN"""
        return self.subscribers.get_subscriber_by_msisdn(msisdn)
    
    def get_subscriber_by_imsi(self, imsi: str) -> Optional[Subscriber]:
        """Get subscriber by IMSI"""
        return self.subscribers.get_subscriber_by_imsi(imsi)
    
    def add_subscriber(self, subscriber: Subscriber):
        """Add subscriber to the registry"""
        self.subscribers.add_subscriber(subscriber)

    # Session management methods
    def add_session(self, app_id: int, session: DiameterSession):
        """Add session and update all indexes"""
        self.sessions[app_id][session.session_id] = session
        
        # Update indexes for Gx sessions
        if app_id == APP_3GPP_GX and isinstance(session, GxSession):
            if session.framed_ip_address:
                self.sessions_by_framed_ip[app_id][session.framed_ip_address] = session.session_id
            if session.framed_ipv6_prefix:
                self.sessions_by_framed_ipv6[app_id][session.framed_ipv6_prefix] = session.session_id
            if session.subscriber and session.subscriber.msisdn:
                self.sessions_by_msisdn[app_id][session.subscriber.msisdn] = session.session_id
    
    def remove_session(self, app_id: int, session_id: str):
        """Remove session and clean up indexes"""
        session = self.sessions[app_id].pop(session_id, None)
        if not session:
            return
            
        # Clean up indexes for Gx sessions
        if app_id == APP_3GPP_GX and isinstance(session, GxSession):
            if session.framed_ip_address:
                self.sessions_by_framed_ip[app_id].pop(session.framed_ip_address, None)
            if session.framed_ipv6_prefix:
                self.sessions_by_framed_ipv6[app_id].pop(session.framed_ipv6_prefix, None)
            if session.subscriber and session.subscriber.msisdn:
                self.sessions_by_msisdn[app_id].pop(session.subscriber.msisdn, None)

    def stage_create_session(self, dm: DiameterMessage):
        app_id = dm.app_id
        session_id = dm.session_id
        # if dm.name not in [CCR_I, AAR, SLR]:
        #     return
        
        # Check if session already exists
        existing_session = self.get_session_by_id(app_id, session_id)
        if existing_session:
            existing_session.add_message(dm)
            return
        
        # Create new session
        if app_id == APP_3GPP_GX:
            session = GxSession(session_id=session_id)
        elif app_id == APP_3GPP_RX:
            session = RxSession(session_id=session_id)
        elif app_id == APP_3GPP_SY:
            session = SySession(session_id=session_id)
        else:
            raise ValueError(f"Unknown app_id: {app_id}")
        
        self.add_session(app_id, session)
        session.add_message(dm)

    def stage_identify_subscriber(self, dm: DiameterMessage) -> Optional[Subscriber]:
        if hasattr(dm.message, 'subscription_id') and dm.message.subscription_id:
            msisdn, imsi, sip_uri, nai, private_id = parse_subscription_id(dm.message.subscription_id)
            subscriber = Subscriber(msisdn=msisdn, imsi=imsi, sip_uri=sip_uri, nai=nai, private_id=private_id)
            self.add_subscriber(subscriber)
            return subscriber
        return None

    def stage_parse_request(self, dm: DiameterMessage):
        self.stage_create_session(dm)
        subscriber = self.stage_identify_subscriber(dm)
        
        # Associate subscriber with session if found
        if subscriber:
            session = self.get_session_by_id(dm.app_id, dm.session_id)
            if session and not session.subscriber:
                session.subscriber = subscriber

    def stage_parse_response(self, dm: DiameterMessage):
        app_id = dm.app_id
        session_id = dm.session_id
        session = self.get_session_by_id(app_id, session_id)
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
  