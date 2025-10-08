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

logger = logging.getLogger("diameter_telecom.session_manager")


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
    save_messages_to_subscriber: bool = True
    save_session_ids_to_subscriber: bool = True
    statistics: dict = field(default_factory=dict)

    def __repr__(self):
        return f"MessageProcessingPipeline(clear_sessions_after_termination={self.clear_sessions_after_termination}, save_messages_to_session={self.save_messages_to_session})"
    
    @timing_decorator
    def main_pipeline(self, context: MessageProcessingContext):
        logger.debug(f"✅ [{context.owner}] Message {context.message.name} entering session_manager.")
        self.stage_get_session(context)
        if context.session:
            logger.debug(context.session)

        if context.message.is_request:
            if not context.session and context.message.name not in REQUESTS_CREATE_SESSION:
                logger.debug(f"✅ [{context.owner}] Message {context.message.name} not in REQUESTS_CREATE_SESSION and no session. Returning False.")
                return False
            elif context.session and not(context.session.n_messages):
                # this means the message is flowing through session_manager
                # it was added to session manager by the client, and the server is during the processing of the message sharing the session manager
                # is this case, lets try allowing the message to flow
                logger.debug(f"✅ [{context.owner}] Message {context.message.name} is flowing through shared session_manager.")
                pass
            self.stage_parse_request(context)
        else:
            if not context.session:
                logger.debug(f"✅ [{context.owner}] Anwer without session. Returning False.")
                return False
            
            self.stage_parse_response(context)
        
        # self.process_app_specific_logic(context)

        
        session: DiameterSession = context.session
        if session and self.save_messages_to_session:
            if context.message not in session.messages:
                session.add_message(context.message)
            else:
                logger.debug(f"✅ [{context.owner}] Message already in session. Returning.")
                pass
            
        subscriber = context.subscriber
        if subscriber:
            if self.save_messages_to_subscriber:
                subscriber.add_message(context.message)
            if self.save_session_ids_to_subscriber:
                subscriber.add_session_id(context.app_id, context.session_id)
            context.message.subscriber = subscriber

        logger.debug(f"✅ [{context.owner}] Message {context.message.name} processed. Leaving session_manager.")
        return True


    def stage_parse_request(self, context: MessageProcessingContext):
        logger.debug(f"✅ [{context.owner}] Stage parse request.")
        if not context.session:
            logger.debug(f"✅ [{context.owner}] No session. Identifying subscriber.")
            self.stage_identify_subscriber(context)
            logger.debug(f"✅ [{context.owner}] Identified subscriber. Creating session.")
            self.stage_create_session(context)
        elif context.session and not context.session.n_messages:
            logger.debug(f"✅ [{context.owner}] Session found but no messages. Continuing.")
            logger.debug(f"✅ [{context.owner}] We should be able to retrieve subscriber from session.")
            if not context.session.subscriber:
                logger.debug(f"✅ [{context.owner}] No subscriber found in session. Identifying subscriber.")
                self.stage_identify_subscriber(context)
            else:
                logger.debug(f"✅ [{context.owner}] Subscriber found in session. Continuing. This might be the case where the DiameterMessage was generated from the DiameterSession as opposed to the DiameterSession generated from the DiameterMessage.")
                context.subscriber = context.session.subscriber
                self.start_session(context)
                if context.app_id == APP_3GPP_RX:
                    self.stage_bind_rx_to_gx(context)
                elif context.app_id == APP_3GPP_SY:
                    self.stage_bind_sy_to_gx(context)
        elif context.session and not context.session.active:
            logger.debug(f"✅ [{context.owner}] Session found and not active. The answer will activate the session. Continuing.")
        elif context.session and context.session.active:
            logger.debug(f"✅ [{context.owner}] Session found and active. Updating session.")
            self.stage_update_session(context)
        else:
            logger.debug(f"✅ [{context.owner}] Session {context.session} found but no information. Continuing.")

    def stage_parse_response(self, context: MessageProcessingContext):
        logger.debug(f"✅ [{context.owner}] Stage parse response.")
        if context.session and not context.session.active and context.session.start_time:
            logger.debug(f"✅ [{context.owner}] Session found and not active and has start time. Activating session.")
            context.session.activate()
            self.start_session(context)
        if context.result_code != E_RESULT_CODE_DIAMETER_SUCCESS:
            logger.debug(f"✅ [{context.owner}] Result code not success. Setting session error.")
            context.session.error = True
        if not context.message.name in RESPONSES_END_SESSION:
            logger.debug(f"✅ [{context.owner}] Message name not in RESPONSES_END_SESSION. Updating session.")
            self.stage_update_session(context)
        else:
            logger.debug(f"✅ [{context.owner}] Message name in RESPONSES_END_SESSION. Ending session.")
            self.stage_end_session(context)



    def stage_get_session(self, context: MessageProcessingContext):
        logger.debug(f"✅ [{context.owner}] Stage get session started")
        app_id = context.app_id
        session_id = context.session_id
        session: DiameterSession | None = self.sessions.get_session_by_id(app_id, session_id)
        if session:
            context.session = session
        if session and session.active:
            context.session_active = True
            logger.debug(f"✅ [{context.owner}] Session found and active. Returning.")
        elif session and session.start_time and not session.active:
            context.session_active = False
            logger.debug(f"✅ [{context.owner}] Session found with start time and started but not active. Returning.")
        else:
            context.session_active = False
            logger.debug(f"✅ [{context.owner}] Session found but not active. Returning.")
        logger.debug(f"✅ [{context.owner}] Stage get session ended")



    def start_session(self, context: MessageProcessingContext):
        logger.debug(f"✅ [{context.owner}] Stage start session.")
        session: DiameterSession = context.session
        session.start(context.message.timestamp)
        logger.debug(f"✅ [{context.owner}] Session started. Returning.")
        return session

    def end_session(self, context: MessageProcessingContext):
        logger.debug(f"✅ [{context.owner}] Stage end session.")
        session: DiameterSession = context.session
        session.end(context.message.timestamp)
        logger.debug(f"✅ [{context.owner}] Session ended. Returning.")
        return session


    def stage_create_session(self, context: MessageProcessingContext):
        logger.debug(f"✅ [{context.owner}] Stage create session")
        logger.debug(f"✅ [{context.owner}] The SessionManager will generate the DiameterSession object from the DiameterMessage.")
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

        self.start_session(context)

        # if not context.subscriber:
        #     context.subscriber = session.subscriber

        # if context.subscriber:
        #     subscriber = context.subscriber
        #     subscriber.add_session_id(app_id, session_id)

        logger.debug(f"✅ [{context.owner}] Adding session to sessions collection.")
        self.sessions.add_session(app_id, session)
        logger.debug(f"✅ [{context.owner}] Session created. Returning.")



    def stage_update_session(self, context: MessageProcessingContext):
        logger.debug(f"✅ [{context.owner}] Stage update session.")
        session: DiameterSession = context.session
        logger.debug(f"✅ [{context.owner}] Session found. Updating session.")
        pass

    def stage_end_session(self, context: MessageProcessingContext):
        logger.debug(f"✅ [{context.owner}] Stage end session.")
        session: DiameterSession = context.session
        logger.debug(f"✅ [{context.owner}] Session found. Ending session.")
        session.end(context.message.timestamp)
        if self.clear_sessions_after_termination:
            logger.debug(f"✅ [{context.owner}] Clearing sessions after termination.")
            self.sessions.remove_session(context.message.app_id, context.message.session_id)
            self._cleanup_session_from_subscriber(session, context.message.app_id)
        logger.debug(f"✅ [{context.owner}] Session ended. Returning.")

    def stage_get_subscriber(self, context: MessageProcessingContext):
        logger.debug(f"✅ [{context.owner}] Stage get subscriber.")
        if context.session:
            context.subscriber = context.session.subscriber
        logger.debug(f"✅ [{context.owner}] Subscriber found. Returning.")

    def stage_create_subscriber(self, context: MessageProcessingContext):
        logger.debug(f"✅ [{context.owner}] Stage create subscriber.")
        subscriber = Subscriber(msisdn=context.msisdn, imsi=context.imsi)
        logger.debug(f"✅ [{context.owner}] Subscriber created. Adding subscriber to subscribers collection.")
        self.subscribers.add_subscriber(subscriber)
        logger.debug(f"✅ [{context.owner}] Subscriber added to subscribers collection. Returning.")
        context.subscriber = subscriber
        logger.debug(f"✅ [{context.owner}] Subscriber added to context. Returning.")
        return subscriber

    def stage_identify_subscriber(self, context: MessageProcessingContext):
        logger.debug(f"✅ [{context.owner}] Stage identify subscriber.")
        subscriber = None  # Initialize to avoid UnboundLocalError
        if context.msisdn:
            logger.debug(f"✅ [{context.owner}] Identifying subscriber by msisdn.")
            subscriber = self.subscribers.get_subscriber_by_msisdn(context.msisdn)
        elif context.imsi:
            logger.debug(f"✅ [{context.owner}] Identifying subscriber by imsi.")
            subscriber = self.subscribers.get_subscriber_by_imsi(context.imsi)
        elif context.framed_ip_address:
            logger.debug(f"✅ [{context.owner}] Identifying subscriber by framed IP address.")
            gx_session = self.sessions.get_session_by_framed_ip(APP_3GPP_GX, context.framed_ip_address)
            if gx_session:
                logger.debug(f"✅ [{context.owner}] Found subscriber by framed IP address.")
                subscriber = gx_session.subscriber
        else:
            logger.debug(f"✅ [{context.owner}] No subscriber identified. Returning.")
            pass
        
        if not subscriber:
            logger.debug(f"✅ [{context.owner}] No subscriber found. Creating subscriber.")
            self.stage_create_subscriber(context)
        else:
            logger.debug(f"✅ [{context.owner}] Subscriber found. Adding to context.")
            context.subscriber = subscriber
        logger.debug(f"✅ [{context.owner}] Stage identify subscriber. Returning.")
        return subscriber

    def stage_bind_rx_to_gx(self, context: MessageProcessingContext):
        logger.debug(f"✅ [{context.owner}] Stage bind rx to gx.")
        dm: DiameterMessage = context.message
        rx_session = context.session
        logger.debug(f"✅ [{context.owner}] Rx session found. Binding rx to gx.")

        # Method 1: Try framed IP address lookup
        if context.framed_ip_address:
            gx_session = self.sessions.get_session_by_framed_ip(APP_3GPP_GX, context.framed_ip_address)
            if gx_session:
                logger.debug(f"✅ [{context.owner}] Found gx session by framed IP address.")
                rx_session.gx_session_id = gx_session.session_id
                rx_session.subscriber = gx_session.subscriber
                gx_session.add_bound_session(APP_3GPP_RX, rx_session.session_id)
                rx_session.add_bound_session(APP_3GPP_GX, gx_session.session_id)
                logger.debug(f"✅ [{context.owner}] Rx session bound to gx session by framed IP address.")
                return
            else:
                logger.debug(f"✅ [{context.owner}] No gx session found by framed IP address.")
                pass
        
        # Method 2: Try subscriber session_ids lookup
        subscriber = context.subscriber
        if subscriber:
            gx_session_id = subscriber.session_ids.get(APP_3GPP_GX)
            if gx_session_id:
                gx_session = self.sessions.get_session_by_id(APP_3GPP_GX, gx_session_id)
                if gx_session:
                    logger.debug(f"✅ [{context.owner}] Found gx session by subscriber session id.")
                    rx_session.gx_session_id = gx_session.session_id
                    rx_session.subscriber = gx_session.subscriber
                    gx_session.add_bound_session(APP_3GPP_RX, rx_session.session_id)
                    rx_session.add_bound_session(APP_3GPP_GX, gx_session.session_id)
                    logger.debug(f"✅ [{context.owner}] Rx session bound to gx session by subscriber session id.")
                    return
                else:
                    # Clean up invalid session ID
                    subscriber.session_ids.pop(APP_3GPP_GX, None)
        

    def stage_bind_sy_to_gx(self, context: MessageProcessingContext):
        # The Sy session is bound using the subscription_id which is already in the context
        sy_session = context.session
        if hasattr(sy_session, 'gx_session_id') and sy_session.gx_session_id:
            logger.debug(f"✅ [{context.owner}] Sy session already bound to gx session. Returning.")
            return
        else:
            logger.debug(f"✅ [{context.owner}] Sy session not bound to gx session. Binding.")

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
