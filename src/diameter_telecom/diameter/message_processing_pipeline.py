# from diameter_telecom.diameter.session._diameter_session import DiameterSession

from dataclasses import field


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
        return result
    return wrapper

@dataclass
class MessageProcessingPipeline:
    sessions: Sessions
    subscribers: Subscribers
    clear_sessions_after_termination: bool = False
    save_messages_to_session: bool = True
    statistics: dict = field(default_factory=dict)

    def __repr__(self):
        return f"MessageProcessingPipeline(clear_sessions_after_termination={self.clear_sessions_after_termination}, save_messages_to_session={self.save_messages_to_session})"
    
    @timing_decorator
    def main_pipeline(self, context: MessageProcessingContext):
        self.stage_get_session(context)
        # if not context.session:
        #     if context.message.name not in REQUESTS_CREATE_SESSION:
        #         return False

        # self.stage_get_subscriber(context)

        if context.message.is_request:
            if not context.session and context.message.name not in REQUESTS_CREATE_SESSION:
                return False
            self.stage_parse_request(context)
        else:
            if not context.session:
                return False
            self.stage_parse_response(context)
        
        # self.process_app_specific_logic(context)
        logger.debug(f"✅ [MAIN PIPELINE] Message {context} processed")
        
        session: DiameterSession = context.session
        if session and self.save_messages_to_session:
            session.messages.append(context.message)
            
        subscriber = context.subscriber
        if subscriber:
            context.message.subscriber = subscriber

        return True


    def stage_parse_request(self, context: MessageProcessingContext):
        if not context.session:
            self.stage_identify_subscriber(context)
            self.stage_create_session(context)
        else:
            self.stage_update_session(context)

    def stage_parse_response(self, context: MessageProcessingContext):
        if context.result_code != E_RESULT_CODE_DIAMETER_SUCCESS:
            context.session.error = True
        if not context.message.name in RESPONSES_END_SESSION:
            self.stage_update_session(context)
        else:
            self.stage_end_session(context)



    def stage_get_session(self, context: MessageProcessingContext):
        app_id = context.app_id
        session_id = context.session_id
        session: DiameterSession | None = self.sessions.get_session_by_id(app_id, session_id)
        if session:
            context.session = session

    def stage_create_session(self, context: MessageProcessingContext):
        dm: DiameterMessage = context.message
        app_id = context.app_id
        session_id = context.session_id
        subscriber = context.subscriber

        framed_ip_address = context.framed_ip_address
        framed_ipv6_prefix = context.framed_ipv6_prefix
        called_station_id = context.called_station_id
        sgsn_mcc_mnc = context.sgsn_mcc_mnc
        
        if app_id == APP_3GPP_GX:
            session = GxSession(session_id=session_id,
                                framed_ip_address=framed_ip_address,
                                framed_ipv6_prefix=framed_ipv6_prefix,
                                called_station_id=called_station_id,
                                sgsn_mcc_mnc=sgsn_mcc_mnc,
                                subscriber=subscriber)
        elif app_id == APP_3GPP_RX:
            session = RxSession(session_id=session_id, subscriber=subscriber)
        elif app_id == APP_3GPP_SY:
            session = SySession(session_id=session_id, subscriber=subscriber)
        else:
            raise ValueError(f"Unknown app_id: {app_id}")

        context.session = session

        if app_id == APP_3GPP_RX:
            self.stage_bind_rx_to_gx(context)
        elif app_id == APP_3GPP_SY:
            self.stage_bind_sy_to_gx(context)

        session.start(dm.timestamp)

        if not context.subscriber:
            context.subscriber = session.subscriber

        if context.subscriber:
            subscriber = context.subscriber
            subscriber.add_session_id(app_id, session_id)

        self.sessions.add_session(app_id, session)

    def stage_update_session(self, context: MessageProcessingContext):
        session: DiameterSession = context.session
        pass

    def stage_end_session(self, context: MessageProcessingContext):
        session: DiameterSession = context.session
        session.end(context.message.timestamp)
        if self.clear_sessions_after_termination:
            self.sessions.remove_session(context.message.app_id, context.message.session_id)
            self._cleanup_session_from_subscriber(session, context.message.app_id)

    def stage_get_subscriber(self, context: MessageProcessingContext):
        if context.session:
            context.subscriber = context.session.subscriber

    def stage_create_subscriber(self, context: MessageProcessingContext):
        subscriber = Subscriber(msisdn=context.msisdn, imsi=context.imsi)
        self.subscribers.add_subscriber(subscriber)
        context.subscriber = subscriber
        return subscriber

    def stage_identify_subscriber(self, context: MessageProcessingContext):
        
        subscriber = None  # Initialize to avoid UnboundLocalError
        if context.msisdn:
            subscriber = self.subscribers.get_subscriber_by_msisdn(context.msisdn)
        elif context.imsi:
            subscriber = self.subscribers.get_subscriber_by_imsi(context.imsi)
        elif context.framed_ip_address:
            gx_session = self.sessions.get_session_by_framed_ip(APP_3GPP_GX, context.framed_ip_address)
            if gx_session:
                subscriber = gx_session.subscriber
        else:
            pass
        
        if not subscriber:
            self.stage_create_subscriber(context)
        else:
            context.subscriber = subscriber

    def stage_bind_rx_to_gx(self, context: MessageProcessingContext):
        dm: DiameterMessage = context.message
        rx_session = context.session
        

        # Method 1: Try framed IP address lookup
        if context.framed_ip_address:
            gx_session = self.sessions.get_session_by_framed_ip(APP_3GPP_GX, context.framed_ip_address)
            if gx_session:
                rx_session.gx_session_id = gx_session.session_id
                rx_session.subscriber = gx_session.subscriber
                gx_session.add_bound_session(APP_3GPP_RX, rx_session.session_id)
                rx_session.add_bound_session(APP_3GPP_GX, gx_session.session_id)
                logger.info(f"✅ [BINDING] RxSession {rx_session.session_id} bound to GxSession {gx_session.session_id} via framed IP {context.framed_ip_address}")
                return
            else:
                pass
        
        # Method 2: Try subscriber session_ids lookup
        subscriber = context.subscriber
        if subscriber:
            gx_session_id = subscriber.session_ids.get(APP_3GPP_GX)
            if gx_session_id:
                gx_session = self.sessions.get_session_by_id(APP_3GPP_GX, gx_session_id)
                if gx_session:
                    rx_session.gx_session_id = gx_session.session_id
                    rx_session.subscriber = gx_session.subscriber
                    gx_session.add_bound_session(APP_3GPP_RX, rx_session.session_id)
                    rx_session.add_bound_session(APP_3GPP_GX, gx_session.session_id)
                    logger.info(f"✅ [BINDING] RxSession {rx_session.session_id} bound to GxSession {gx_session.session_id} via subscriber {subscriber.msisdn}")
                    return
                else:
                    # Clean up invalid session ID
                    subscriber.session_ids.pop(APP_3GPP_GX, None)
        

    def stage_bind_sy_to_gx(self, context: MessageProcessingContext):
        # The Sy session is bound using the subscription_id which is already in the context
        sy_session = context.session
        msisdn, imsi = context.msisdn, context.imsi
        if msisdn:
            gx_session = self.sessions.get_session_by_msisdn(APP_3GPP_GX, msisdn)
            if gx_session:
                sy_session.gx_session_id = gx_session.session_id
                sy_session.subscriber = gx_session.subscriber
                gx_session.add_bound_session(APP_3GPP_SY, sy_session.session_id)
                sy_session.add_bound_session(APP_3GPP_GX, gx_session.session_id)
                logger.info(f"✅ [BINDING] SySession {sy_session.session_id} bound to GxSession {gx_session.session_id} via msisdn {msisdn}")
                return
            else:
                pass
        elif imsi:
            gx_session = self.sessions.get_session_by_imsi(APP_3GPP_GX, imsi)
            if gx_session:
                sy_session.gx_session_id = gx_session.session_id
                sy_session.subscriber = gx_session.subscriber
                gx_session.add_bound_session(APP_3GPP_SY, sy_session.session_id)
                sy_session.add_bound_session(APP_3GPP_GX, gx_session.session_id)
                logger.info(f"✅ [BINDING] SySession {sy_session.session_id} bound to GxSession {gx_session.session_id} via imsi {imsi}")
                return
            else:
                pass
        else:
            pass

        logger.warning(f"❌ [BINDING] SySession {sy_session.session_id} not bound to GxSession")
    
    
    # def stage_process_gx_message(self, context: MessageProcessingContext):
    #     dm: DiameterMessage = context.message
    #     session: GxSession = context.session
        
        
    #     if dm.is_request:
    #         if dm.name == CCR_I:
    #             pass
    #             # Extract session attributes from CCR-I
    #             # if dm.timestamp and not session.start_time:
    #             #     session.start_time = dm.timestamp
    #             # if hasattr(dm.message, 'framed_ip_address') and dm.message.framed_ip_address and not session.framed_ip_address:
    #             #     session.framed_ip_address = dm.message.framed_ip_address
    #             # if hasattr(dm.message, 'framed_ipv6_prefix') and dm.message.framed_ipv6_prefix and not session.framed_ipv6_prefix:
    #             #     session.framed_ipv6_prefix = dm.message.framed_ipv6_prefix
    #             # if hasattr(dm.message, 'called_station_id') and dm.message.called_station_id and not session.called_station_id:
    #             #     session.called_station_id = dm.message.called_station_id
    #             # if hasattr(dm.message, 'sgsn_mcc_mnc') and dm.message.sgsn_mcc_mnc and not session.sgsn_mcc_mnc:
    #             #     session.sgsn_mcc_mnc = dm.message.sgsn_mcc_mnc
    #     else:
    #         # Process response messages - use common error handling
    #         self._handle_result_code_errors(session, dm)
            
    #         if dm.name == CCA_I:
    #             if dm.timestamp and dm.message.result_code == E_RESULT_CODE_DIAMETER_SUCCESS:
    #                 session.active = True
    #         elif dm.name == CCA_T:
    #             if dm.timestamp:
    #                 session.active = False
    #                 session.ended = True
    #                 session.end_time = dm.timestamp
    #                 # Clean up session from both subscriber tracking and session manager
    #                 self._cleanup_session_from_subscriber(session, APP_3GPP_GX)
        
    #     # Update common attributes
    #     if hasattr(dm.message, 'cc_request_number') and dm.message.cc_request_number is not None:
    #         session.cc_request_number = dm.message.cc_request_number

    #     if hasattr(dm.message, 'sgsn_mcc_mnc') and dm.message.sgsn_mcc_mnc:
    #         session.sgsn_mcc_mnc = dm.message.sgsn_mcc_mnc
        

    def _cleanup_session_from_subscriber(self, session: DiameterSession, app_id: int):
        
        if session.subscriber and session.session_id:
            # todo: we are assuming there is only one session per app_id for the subscriber
            removed_session_id = session.subscriber.session_ids.pop(app_id, None)
            if removed_session_id:
                pass
            else:
                pass
        else:
            pass
        
        # Also remove the session from the Sessions collection
        self.sessions.remove_session(app_id, session.session_id)

    # def _handle_session_start(self, session: DiameterSession, message: DiameterMessage, start_message_type: str):
    #     if message.name == start_message_type:
    #         if message.timestamp:
    #             session.start(message.timestamp)
    #         else:
    #             session.start()

    # def _handle_session_end(self, session: DiameterSession, message: DiameterMessage, context: MessageProcessingContext):
    #     if message.name == STR:
    #         if message.timestamp:
    #             session.end(message.timestamp)
    #         else:
    #             session.end()
    #         # Clean up session from both subscriber tracking and session manager
    #         self._cleanup_session_from_subscriber(session, message.app_id)


    # def _handle_result_code_errors(self, session: DiameterSession, message: DiameterMessage):
        
    #     if (hasattr(message.message, 'result_code') and 
    #         message.message.result_code and 
    #         message.message.result_code != E_RESULT_CODE_DIAMETER_SUCCESS):
    #         session.error = True
    #         logger.warning(f"⚠️ [ERROR] Session {session.session_id} marked as error due to result code: {message.message.result_code}")
    #         # Clean up error sessions from both subscriber tracking and session manager
    #         # self._cleanup_session_from_subscriber(session, message.app_id)
    #     else:
    #         pass

    # def stage_process_rx_message(self, context: MessageProcessingContext):
    #     dm: DiameterMessage = context.message
    #     session: RxSession = context.session
        
        
    #     if dm.is_request:
    #         # Handle session start
    #         self._handle_session_start(session, dm, AAR)
    #         # Handle session end
    #         self._handle_session_end(session, dm, context)
    #     else:
    #         # Handle response errors (NEW for Rx sessions)
    #         self._handle_result_code_errors(session, dm)
        

    # def stage_process_sy_message(self, context: MessageProcessingContext):
    #     dm: DiameterMessage = context.message
    #     session: SySession = context.session
        
        
    #     if dm.is_request:
    #         # Handle session start
    #         self._handle_session_start(session, dm, SLR)
    #         # Handle session end
    #         self._handle_session_end(session, dm, context)
    #     else:
    #         # Handle response errors (NEW for Sy sessions)
    #         self._handle_result_code_errors(session, dm)
        

    # def process_app_specific_logic(self, context: MessageProcessingContext):
    #     dm = context.message
    #     session = context.session
        
        
    #     if session:
    #         if dm.app_id == APP_3GPP_GX:
    #             self.stage_process_gx_message(context)
    #         elif dm.app_id == APP_3GPP_RX:
    #             self.stage_process_rx_message(context)
    #         elif dm.app_id == APP_3GPP_SY:
    #             self.stage_process_sy_message(context)
    #         else:
    #             pass
    #     else:
    #         pass
