from diameter_telecom.diameter.session._diameter_session import DiameterSession


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
END_SESSION_MESSAGES = [STA, CCA_T]

import time
import functools

import time
import functools

def timing_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        elapsed_microseconds = (end - start) * 1_000_000  # Convert seconds to microseconds
        
        # If this is process_diameter_message, set processing time on DiameterMessage
        if func.__name__ == 'main_pipeline' and len(args) >= 2:
            context = args[1]
            diameter_message = context.message
            diameter_message.processing_time_microseconds = elapsed_microseconds
            logger.debug(f"Processed {diameter_message.name} ({diameter_message.session_id}) in {elapsed_microseconds:.0f}μs")
        elif func.__name__ == '_write_context_to_csv':
            logger.debug(f"CSV write completed in {elapsed_microseconds:.0f}μs")
        else:
            logger.debug(f"{func.__name__} completed in {elapsed_microseconds:.0f}μs")
        return result
    return wrapper

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
    
    @timing_decorator
    def main_pipeline(self, context: MessageProcessingContext):
        """Main pipeline for processing Diameter messages"""
        self.stage_get_session(context)
        if not context.session:
            if context.message.name not in CREATE_SESSION_MESSAGES:
                return False

        self.stage_get_subscriber(context)

        # Delegate to pipeline for processing (uses fine-grained locks internally)
        if context.message.is_request:
            self.stage_parse_request(context)
        else:
            self.stage_parse_response(context)
        
        # Process application-specific business logic (uses fine-grained locks internally)
        self.process_app_specific_logic(context)
        
        # Handle final message storage and association
        session: DiameterSession = context.session
        if session:
            # Session.messages is per-session - no contention between different sessions
            session.messages.append(context.message)
            
            subscriber = context.subscriber
            if subscriber:
                context.message.subscriber = subscriber

        return True


    def stage_get_session(self, context: MessageProcessingContext):
        """Retrieve existing session from storage"""
        app_id = context.app_id
        session_id = context.session_id
        session: DiameterSession | None = self.sessions.get_session_by_id(app_id, session_id)
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

        if hasattr(dm.message, 'framed_ip_address') and dm.message.framed_ip_address:
            framed_ip_address = dm.message.framed_ip_address
            # if isinstance(framed_ip_address, bytes):
            framed_ip_address = bytes_to_ip(framed_ip_address)
            context.framed_ip_address = framed_ip_address
        if hasattr(dm.message, 'framed_ipv6_prefix') and dm.message.framed_ipv6_prefix:
            framed_ipv6_prefix = dm.message.framed_ipv6_prefix
        if hasattr(dm.message, 'called_station_id') and dm.message.called_station_id:
            called_station_id = dm.message.called_station_id
        if hasattr(dm.message, 'sgsn_mcc_mnc') and dm.message.sgsn_mcc_mnc:
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

        session.start(dm.timestamp)

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
        if not context.subscriber:
            self.stage_identify_subscriber(context)
        if not context.session:
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
            # Process response messages - use common error handling
            self._handle_result_code_errors(session, dm)
            
            if dm.name == CCA_I:
                if dm.timestamp and dm.message.result_code == E_RESULT_CODE_DIAMETER_SUCCESS:
                    session.active = True
            elif dm.name == CCA_T:
                if dm.timestamp:
                    session.active = False
                    session.ended = True
                    session.end_time = dm.timestamp
                    # Clean up session from both subscriber tracking and session manager
                    self._cleanup_session_from_subscriber(session, APP_3GPP_GX)
        
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
        
        # Also remove the session from the Sessions collection
        self.sessions.remove_session(app_id, session.session_id)
        logger.info(f"Session {session.session_id} removed from session manager")

    def _handle_session_start(self, session: DiameterSession, message: DiameterMessage, start_message_type: str):
        """Common logic for session start with timestamp handling"""
        if message.name == start_message_type:
            if message.timestamp:
                session.start(message.timestamp)
            else:
                session.start()

    def _handle_session_end(self, session: DiameterSession, message: DiameterMessage, context: MessageProcessingContext):
        """Common logic for session end with cleanup"""
        if message.name == STR:
            if message.timestamp:
                session.end(message.timestamp)
            else:
                session.end()
            # Clean up session from both subscriber tracking and session manager
            self._cleanup_session_from_subscriber(session, message.app_id)

    def _handle_result_code_errors(self, session: DiameterSession, message: DiameterMessage):
        """Common error handling for all session types"""
        if (hasattr(message.message, 'result_code') and 
            message.message.result_code and 
            message.message.result_code != E_RESULT_CODE_DIAMETER_SUCCESS):
            session.error = True
            logger.warning(f"Session {session.session_id} marked as error due to result code: {message.message.result_code}")
            # Clean up error sessions from both subscriber tracking and session manager
            self._cleanup_session_from_subscriber(session, message.app_id)

    def stage_process_rx_message(self, context: MessageProcessingContext):
        """Process Rx-specific message business logic"""
        dm: DiameterMessage = context.message
        session: RxSession = context.session
        
        if dm.is_request:
            # Handle session start
            self._handle_session_start(session, dm, AAR)
            # Handle session end
            self._handle_session_end(session, dm, context)
        else:
            # Handle response errors (NEW for Rx sessions)
            self._handle_result_code_errors(session, dm)

    def stage_process_sy_message(self, context: MessageProcessingContext):
        """Process Sy-specific message business logic"""
        dm: DiameterMessage = context.message
        session: SySession = context.session
        
        if dm.is_request:
            # Handle session start
            self._handle_session_start(session, dm, SLR)
            # Handle session end
            self._handle_session_end(session, dm, context)
        else:
            # Handle response errors (NEW for Sy sessions)
            self._handle_result_code_errors(session, dm)

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
