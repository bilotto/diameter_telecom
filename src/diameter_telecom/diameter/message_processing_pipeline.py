from ..subscriber import Subscriber, Subscribers
from .session import GxSession, RxSession, SySession, DiameterSession
from .session.sessions import Sessions
from .message_processing_context import MessageProcessingContext
from typing import Optional
from dataclasses import dataclass
import logging
from .constants import *
from .parse_avp import *
from .message import DiameterMessage

logger = logging.getLogger(__name__)

CREATE_SESSION_MESSAGES = [CCR_I, AAR, SLR]

@dataclass
class MessageProcessingPipeline:
    """
    Handles all message processing stages for Diameter messages.
    
    This class contains the pipeline logic for processing Diameter messages,
    including session management, subscriber identification, and application-specific
    business logic. It operates on a MessageProcessingContext that flows
    through all processing stages.
    """
    sessions: Sessions
    subscribers: Subscribers

    def stage_get_session(self, context: MessageProcessingContext):
        """Retrieve existing session from storage"""
        app_id = context.app_id
        session_id = context.session_id
        session = self.sessions.get_session_by_id(app_id, session_id)
        if session:
            context.session = session

    def stage_create_session(self, context: MessageProcessingContext):
        """Create a new session for the message"""
        dm: DiameterMessage = context.message
        app_id = context.app_id
        session_id = context.session_id
        subscriber = context.subscriber

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

        context.session = session

        # Bind Rx/Sy sessions to Gx sessions after creation
        if app_id == APP_3GPP_RX:
            self.stage_bind_rx_to_gx(context)
        elif app_id == APP_3GPP_SY:
            self.stage_bind_sy_to_gx(context)

        if not context.subscriber:
            context.subscriber = session.subscriber

        # Update subscriber's session_ids tracking if subscriber exists
        if context.subscriber:
            subscriber = context.subscriber
            subscriber.add_session_id(app_id, session_id)
            logger.debug(f"Updated subscriber {subscriber.msisdn} session_ids: {subscriber.session_ids}")

        self.sessions.add_session(app_id, session)

    def stage_get_subscriber(self, context: MessageProcessingContext):
        """Get subscriber from existing session if available"""
        if context.session and context.session.subscriber:
            subscriber = context.session.subscriber
            context.subscriber = subscriber

    def stage_identify_subscriber(self, context: MessageProcessingContext):
        """Identify subscriber from message content"""
        dm = context.message
        if hasattr(dm.message, 'subscription_id') and dm.message.subscription_id:
            msisdn, imsi, sip_uri, nai, private_id = parse_subscription_id(dm.message.subscription_id)
            subscriber = self.subscribers.get_subscriber_by_msisdn(msisdn) or self.subscribers.get_subscriber_by_imsi(imsi)
            if not subscriber:
                subscriber = Subscriber(msisdn=msisdn, imsi=imsi, sip_uri=sip_uri, nai=nai, private_id=private_id)
                self.subscribers.add_subscriber(subscriber)
            context.subscriber = subscriber
        else:
            logger.warning(f"No subscriber found for message: {dm.name}")

    def stage_parse_request(self, context: MessageProcessingContext):
        """Process request message through the pipeline stages"""
        dm = context.message
        self.stage_get_session(context)
        self.stage_get_subscriber(context)
        if not context.subscriber:
            self.stage_identify_subscriber(context)
        if not context.session and dm.name in CREATE_SESSION_MESSAGES:
            self.stage_create_session(context)

    def stage_parse_response(self, context: MessageProcessingContext):
        """Process response message through the pipeline stages"""
        dm = context.message
        self.stage_get_session(context)
        self.stage_get_subscriber(context)
        if not context.session:
            logger.warning(f"No session found for response: {dm.name},{dm.session_id}")

    def stage_bind_rx_to_gx(self, context: MessageProcessingContext):
        """Bind RxSession to existing GxSession based on identifiers"""
        dm: DiameterMessage = context.message
        rx_session = context.session

        if hasattr(dm.message, 'framed_ip_address') and dm.message.framed_ip_address:
            logger.debug(f"Trying to find GxSession by framed IP address: {dm.message.framed_ip_address}")
            gx_session = self.sessions.get_session_by_framed_ip(APP_3GPP_GX, dm.message.framed_ip_address)
            if gx_session:
                rx_session.gx_session_id = gx_session.session_id
                rx_session.subscriber = gx_session.subscriber
                logger.info(f"RxSession {rx_session.session_id} bound to GxSession {gx_session.session_id} via framed IP {dm.message.framed_ip_address}")
                return
        
        # Try to find GxSession via subscriber if available
        subscriber = context.subscriber
        if subscriber:
            gx_session_id = subscriber.session_ids.get(APP_3GPP_GX)
            if gx_session_id:
                gx_session = self.sessions.get_session_by_id(APP_3GPP_GX, gx_session_id)
                if gx_session:
                    rx_session.gx_session_id = gx_session.session_id
                    rx_session.subscriber = gx_session.subscriber
                    logger.info(f"RxSession {rx_session.session_id} bound to GxSession {gx_session.session_id} via subscriber {subscriber.msisdn}")
                    return
                else:
                    # Clean up invalid session ID
                    subscriber.session_ids.pop(APP_3GPP_GX, None)
        
        # Fallback: try MSISDN-based lookup (legacy approach)
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

    def stage_bind_sy_to_gx(self, context: MessageProcessingContext):
        """Bind SySession to existing active GxSession for the same subscriber"""
        dm: DiameterMessage = context.message
        sy_session = context.session
        subscriber = context.subscriber
        
        if not subscriber:
            logger.warning(f"No subscriber found for SySession {sy_session.session_id}, cannot bind to GxSession")
            return
        
        # Check if subscriber has a Gx session ID
        gx_session_id = subscriber.session_ids.get(APP_3GPP_GX)
        if not gx_session_id:
            logger.warning(f"No GxSession ID found in subscriber {subscriber.msisdn} for SySession {sy_session.session_id}")
            return
        
        # Get the Gx session directly using the ID
        gx_session = self.sessions.get_session_by_id(APP_3GPP_GX, gx_session_id)
        if not gx_session:
            logger.warning(f"GxSession {gx_session_id} not found for SySession {sy_session.session_id} with subscriber {subscriber.msisdn}")
            # Clean up the invalid session ID from subscriber
            subscriber.session_ids.pop(APP_3GPP_GX, None)
            return
        
        # Bind the Sy session to the Gx session
        sy_session.gx_session_id = gx_session.session_id
        sy_session.subscriber = gx_session.subscriber
        
        if gx_session.active:
            logger.info(f"SySession {sy_session.session_id} bound to active GxSession {gx_session.session_id} for subscriber {subscriber.msisdn}")
        else:
            logger.info(f"SySession {sy_session.session_id} bound to GxSession {gx_session.session_id} (not active) for subscriber {subscriber.msisdn}")

    def stage_process_gx_message(self, context: MessageProcessingContext):
        """Process Gx-specific message business logic"""
        dm: DiameterMessage = context.message
        session: GxSession = context.session
        
        if dm.is_request:
            if dm.name == CCR_I:
                # Extract session attributes from CCR-I
                if dm.timestamp and not session.start_time:
                    session.start_time = dm.timestamp
                if hasattr(dm.message, 'framed_ip_address') and dm.message.framed_ip_address and not session.framed_ip_address:
                    session.framed_ip_address = dm.message.framed_ip_address
                if hasattr(dm.message, 'framed_ipv6_prefix') and dm.message.framed_ipv6_prefix and not session.framed_ipv6_prefix:
                    session.framed_ipv6_prefix = dm.message.framed_ipv6_prefix
                if hasattr(dm.message, 'called_station_id') and dm.message.called_station_id and not session.called_station_id:
                    session.called_station_id = dm.message.called_station_id
                if hasattr(dm.message, 'sgsn_mcc_mnc') and dm.message.sgsn_mcc_mnc and not session.sgsn_mcc_mnc:
                    session.sgsn_mcc_mnc = dm.message.sgsn_mcc_mnc
        else:
            # Process response messages
            if hasattr(dm.message, 'result_code') and dm.message.result_code and dm.message.result_code != E_RESULT_CODE_DIAMETER_SUCCESS:
                session.error = True
                # Clean up session ID from subscriber when session has error
                # self._cleanup_session_from_subscriber(session, APP_3GPP_GX)
            
            if dm.name == CCA_I:
                if dm.timestamp and dm.message.result_code == E_RESULT_CODE_DIAMETER_SUCCESS:
                    session.active = True
            elif dm.name == CCA_T:
                if dm.timestamp:
                    session.active = False
                    session.ended = True
                    session.end_time = dm.timestamp
                    # Clean up session ID from subscriber
                    # self._cleanup_session_from_subscriber(session, APP_3GPP_GX)
        
        # Update common attributes
        if hasattr(dm.message, 'cc_request_number') and dm.message.cc_request_number is not None:
            session.cc_request_number = dm.message.cc_request_number

        if hasattr(dm.message, 'sgsn_mcc_mnc') and dm.message.sgsn_mcc_mnc:
            session.sgsn_mcc_mnc = dm.message.sgsn_mcc_mnc

    def _cleanup_session_from_subscriber(self, session: DiameterSession, app_id: int):
        """Remove session ID from subscriber's session_ids when session ends"""
        if session.subscriber and session.session_id:
            removed_session_id = session.subscriber.session_ids.pop(app_id, None)
            if removed_session_id:
                logger.debug(f"Cleaned up session {removed_session_id} from subscriber {session.subscriber.msisdn} session_ids: {session.subscriber.session_ids}")

    def stage_process_rx_message(self, context: MessageProcessingContext):
        """Process Rx-specific message business logic"""
        dm: DiameterMessage = context.message
        session: RxSession = context.session
        
        if dm.name == AAR:
            if dm.timestamp:
                session.start(dm.timestamp)
            else:
                session.start()
        elif dm.name == STR:
            if dm.timestamp:
                session.end(dm.timestamp)
            else:
                session.end()
            # Clean up session ID from subscriber
            # self._cleanup_session_from_subscriber(session, APP_3GPP_RX)

    def stage_process_sy_message(self, context: MessageProcessingContext):
        """Process Sy-specific message business logic"""
        dm: DiameterMessage = context.message
        session: SySession = context.session
        
        if dm.name == SLR:
            if dm.timestamp:
                session.start(dm.timestamp)
        elif dm.name == STR:
            if dm.timestamp:
                session.end(dm.timestamp)
            else:
                session.end()
            # Clean up session ID from subscriber
            # self._cleanup_session_from_subscriber(session, APP_3GPP_SY)

    def process_app_specific_logic(self, context: MessageProcessingContext):
        """Route to application-specific processing"""
        dm = context.message
        session = context.session
        
        if session:
            if dm.app_id == APP_3GPP_GX:
                self.stage_process_gx_message(context)
            elif dm.app_id == APP_3GPP_RX:
                self.stage_process_rx_message(context)
            elif dm.app_id == APP_3GPP_SY:
                self.stage_process_sy_message(context)
