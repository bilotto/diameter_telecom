from ..subscriber import Subscriber, Subscribers
from .session import GxSession, RxSession, SySession, DiameterSession
from .session.sessions import Sessions
from .message_processing_pipeline import MessageProcessingPipeline
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
    """Centralized session and subscriber management for Diameter applications.
    
    This class handles high-level orchestration of message processing and maintains
    the data stores for sessions, subscribers, and messages. The actual message 
    processing logic is delegated to MessageProcessingPipeline.
    """
    sessions: Sessions = field(default_factory=Sessions)
    subscribers: Subscribers = field(default_factory=Subscribers)
    messages: List[DiameterMessage] = field(default_factory=list)
    pipeline: MessageProcessingPipeline = field(init=False)

    def __post_init__(self):
        """Initialize the message processing pipeline"""
        self.pipeline = MessageProcessingPipeline(
            sessions=self.sessions,
            subscribers=self.subscribers
        )

    def get_messages(self):
        return sorted(self.messages, key=lambda x: x.timestamp if x.timestamp else float('inf'))

    def process_diameter_message(self, dm: DiameterMessage):
        """Main entry point for processing Diameter messages.
        
        This method orchestrates the message processing by delegating to the
        MessageProcessingPipeline and handling the final message storage.
        """
        # Setup processing context
        gv_stages = dict()
        if not dm.timestamp:
            dm.timestamp = time.time()
        gv_stages['dm'] = dm
        gv_stages['session_id'] = dm.session_id
        gv_stages['app_id'] = dm.app_id
        print(f"Processing {dm.name} - {dm.session_id}")
        
        # Delegate to pipeline for processing
        if dm.is_request:
            self.pipeline.stage_parse_request(gv_stages)
        else:
            self.pipeline.stage_parse_response(gv_stages)
        
        # Process application-specific business logic
        self.pipeline.process_app_specific_logic(gv_stages)
        
        # Handle final message storage and association
        session = gv_stages.get('session')
        if session:
            session.messages.append(dm)
            subscriber = gv_stages.get('subscriber')
            if subscriber:
                subscriber.add_message(dm)
                dm.subscriber = subscriber

        self.messages.append(dm)

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
