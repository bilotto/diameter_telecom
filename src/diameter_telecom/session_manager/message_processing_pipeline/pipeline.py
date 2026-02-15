from dataclasses import dataclass, field
import logging

from .constants import *
from .decorators import timing_decorator
from .validation import ValidationStage
from .session_resolution import SessionResolutionStage
from .subscriber_resolution import SubscriberResolutionStage
from .session_creation import SessionCreationStage
from .session_start import SessionStartStage
from .session_binding import SessionBindingStage
from .session_refresh import SessionRefreshStage
from .session_terminate import SessionTerminateStage
from .session_update import SessionUpdateStage
from .error_handling import ErrorHandlingStage
from .message_storage import MessageStorageStage
from .cleanup import CleanupStage
from .base import ProcessingStage

from ..sessions import Sessions
from ...subscriber import Subscribers
from ..message_processing_context import MessageProcessingContext

logger = logging.getLogger("diameter_telecom.session_manager")


@dataclass
class MessageProcessingPipeline:
    """Clean, stage-based message processing pipeline."""
    
    sessions: Sessions
    subscribers: Subscribers
    clear_sessions_after_termination: bool = False
    save_messages_to_session: bool = True
    save_messages_to_subscriber: bool = False
    save_session_ids_to_subscriber: bool = False
    enable_session_binding: bool = True
    statistics: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize the processing stages."""
        self.stages = {
            STAGE_VALIDATION: ValidationStage(),           # Validate message and context
            STAGE_SESSION_RESOLUTION: SessionResolutionStage(),    # Find existing session
            STAGE_SUBSCRIBER_RESOLUTION: SubscriberResolutionStage(), # Find/create subscriber  
            STAGE_SESSION_CREATION: SessionCreationStage(),      # Create new session for START flow
            STAGE_SESSION_START: SessionStartStage(),         # Start session for START flow
            STAGE_SESSION_BINDING: SessionBindingStage(),       # Bind Rx/Sy to Gx sessions
            STAGE_SESSION_REFRESH: SessionRefreshStage(),       # Handle REFRESH flow (RAR, ASR)
            STAGE_SESSION_TERMINATE: SessionTerminateStage(),     # Handle TERMINATE flow (CCR-T, STR)
            STAGE_SESSION_UPDATE: SessionUpdateStage(),       # Update session for UPDATE flow
            STAGE_ERROR_HANDLING: ErrorHandlingStage(),        # Handle error responses for all messages
            STAGE_MESSAGE_STORAGE: MessageStorageStage(),      # Store message in session/subscriber
            STAGE_CLEANUP: CleanupStage()              # Cleanup and finalize
        }
    
    def __repr__(self):
        return f"MessageProcessingPipeline(clear_sessions_after_termination={self.clear_sessions_after_termination}, save_messages_to_session={self.save_messages_to_session}, enable_session_binding={self.enable_session_binding})"
    
    @timing_decorator
    def main_pipeline(self, context: MessageProcessingContext) -> bool:
        """Main entry point for message processing."""
        logger.debug(f"🚀 Starting pipeline processing for message {context.message.name}")
        
        # Add collections to context so stages can access them
        context.sessions = self.sessions
        context.subscribers = self.subscribers
        context.clear_sessions_after_termination = self.clear_sessions_after_termination
        context.save_messages_to_session = self.save_messages_to_session
        context.save_messages_to_subscriber = self.save_messages_to_subscriber
        context.save_session_ids_to_subscriber = self.save_session_ids_to_subscriber
        context.enable_session_binding = self.enable_session_binding
        
        try:
            # Always run validation first
            self.stages[STAGE_VALIDATION].execute(context)
            if getattr(context, 'should_stop', False):
                logger.debug(f"🛑 Pipeline stopped at ValidationStage")
                return True
            
            # Always run session resolution second
            self.stages[STAGE_SESSION_RESOLUTION].execute(context)
            if getattr(context, 'should_stop', False):
                logger.debug(f"🛑 Pipeline stopped at SessionResolutionStage")
                return True
            
            # Now we can make smart decisions based on session state
            self._run_smart_stages(context)
                    
            logger.debug(f"✅ Pipeline processing completed for message {context.message.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Pipeline processing failed for message {context.message.name}: {e}")
            return False
    
    def _run_smart_stages(self, context: MessageProcessingContext):
        """Run stages based on session state and message type."""
        
        # If we already have subscriber from session, skip SubscriberResolutionStage
        if not context.subscriber_found:
            logger.debug(f"🎯 Smart routing: Need to resolve subscriber")
            self.stages[STAGE_SUBSCRIBER_RESOLUTION].execute(context)
        else:
            logger.debug(f"🎯 Smart routing: Skipping SubscriberResolutionStage - subscriber already found")

        if context.message_flow_type == FLOW_START:
            # New session flow
            if not context.session_found:
                logger.debug(f"🎯 Smart routing: START flow - creating session")
                self.stages[STAGE_SESSION_CREATION].execute(context)
            else:
                logger.debug(f"🎯 Smart routing: START flow but session exists")
            #
            self.stages[STAGE_SESSION_START].execute(context)
            self.stages[STAGE_SESSION_BINDING].execute(context)

        elif context.message_flow_type == FLOW_UPDATE:
            # Update session flow
            if context.session_found:
                logger.debug(f"🎯 Smart routing: UPDATE flow - updating session")
                self.stages[STAGE_SESSION_UPDATE].execute(context)
            else:
                logger.debug(f"🎯 Smart routing: UPDATE flow but no session - skipping update")

        elif context.message_flow_type == FLOW_REFRESH:
            # Refresh session flow
            if context.session_found:
                logger.debug(f"🎯 Smart routing: REFRESH flow - refreshing session")
                self.stages[STAGE_SESSION_REFRESH].execute(context)
            else:
                logger.debug(f"🎯 Smart routing: REFRESH flow but no session - skipping refresh")

        elif context.message_flow_type == FLOW_TERMINATE:
            # Terminate session flow
            if context.session_found:
                logger.debug(f"🎯 Smart routing: TERMINATE flow - terminating session")
                self.stages[STAGE_SESSION_TERMINATE].execute(context)
            else:
                logger.debug(f"🎯 Smart routing: TERMINATE flow but no session - skipping termination")
        else:
            # Unknown flow type
            logger.debug(f"🎯 Smart routing: Unknown flow type {context.message_flow_type} - updating session if available")
            if context.session_found:
                self.stages[STAGE_SESSION_UPDATE].execute(context)
        
        # Always run error handling for response messages (regardless of flow type)
        self.stages[STAGE_ERROR_HANDLING].execute(context)
        
        # Always run message storage and cleanup
        self.stages[STAGE_MESSAGE_STORAGE].execute(context)
        self.stages[STAGE_CLEANUP].execute(context)
    
    def handle_stage_error(self, stage: ProcessingStage, context: MessageProcessingContext, error: Exception):
        """Handle errors that occur during stage processing."""
        logger.error(f"❌ [{stage.name}] Stage failed: {error}")
        # TODO: Add error recovery logic
        pass
