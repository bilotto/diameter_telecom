from dataclasses import dataclass, field
from typing import Optional, List, Any
import logging
import time
import functools

from ..subscriber import Subscriber, Subscribers
from ..session._diameter_session import DiameterSession
from ..session.gx import GxSession
from ..session.rx import RxSession
from ..session.sy import SySession
from .sessions import Sessions
from .message_processing_context import MessageProcessingContext
from ..constants import *
from ..message import DiameterMessage

logger = logging.getLogger("diameter_telecom.session_manager")

# Base Stage Class
class ProcessingStage:
    """Base class for all processing stages."""
    
    def __init__(self, name: str):
        self.name = name
    
    def execute(self, context: MessageProcessingContext) -> None:
        """Execute this stage. Override in subclasses."""
        logger.debug(f"🔧 [{self.name}] Stage executed (dummy implementation)")
        pass
    
    def log_stage(self, context: MessageProcessingContext, level: str, message: str):
        """Helper method for consistent stage logging."""
        owner = getattr(context, 'owner_key', None) or "Unknown"
        prefix = f"[{owner}] [{self.name}]"
        full_message = f"{prefix} {message}"
        
        if level == "debug":
            logger.debug(full_message)
        elif level == "info":
            logger.info(full_message)
        elif level == "warning":
            logger.warning(full_message)
        elif level == "error":
            logger.error(full_message)

# Individual Stage Implementations (Dummy)
# Individual Stage Implementations (Real Logic)
class ValidationStage(ProcessingStage):
    """Validates message and context before processing."""
    
    def __init__(self):
        super().__init__("VALIDATION")
    
    def execute(self, context: MessageProcessingContext) -> None:
        """Validate message and context before processing."""
        self.log_stage(context, "debug", f"✅ Validating message {context.message.name} with session_id {context.session_id}")
        
        validation_errors = []
        
        # Validate message is not None
        if not context.message:
            validation_errors.append("Message is None")
            self.log_stage(context, "error", "❌ Validation failed: Message is None")
            context.should_stop = True
            return
        
        # Validate session_id is not empty
        if not context.session_id:
            validation_errors.append("Session ID is empty")
            self.log_stage(context, "error", "❌ Validation failed: Session ID is empty")
            context.should_stop = True
            return
        
        # Validate app_id is valid
        valid_app_ids = [APP_3GPP_GX, APP_3GPP_RX, APP_3GPP_SY]
        if context.app_id not in valid_app_ids:
            validation_errors.append(f"Invalid app_id: {context.app_id}")
            self.log_stage(context, "error", f"❌ Validation failed: Invalid app_id {context.app_id}")
            context.should_stop = True
            return
        
        # Check if message should be processed (skip messages from same host)
        # This logic was in the original SessionManager.process_diameter_message
        try:
            owner_app = getattr(context, 'owner_app', None)
            if owner_app and hasattr(owner_app, 'node') and hasattr(owner_app.node, 'origin_host'):
                owner_origin_host = owner_app.node.origin_host
                message_origin_host = context.origin_host
                if owner_origin_host and message_origin_host and message_origin_host == owner_origin_host:
                    self.log_stage(context, "info", f"🔄 Message comes from the host itself. Skipping processing.")
                    context.should_stop = True
                    return
        except Exception as e:
            self.log_stage(context, "debug", f"⚠️ Could not check origin host: {e}")
        
        # Validate message has required fields for session creation
        if context.message.is_request and context.message.name not in REQUESTS_CREATE_SESSION:
            # This is not an error, but we need to ensure we have a session
            self.log_stage(context, "debug", f"📋 Message {context.message.name} not in REQUESTS_CREATE_SESSION - will need existing session")
        
        # Set validation results
        context.validated = True
        context.validation_errors = validation_errors
        
        if validation_errors:
            self.log_stage(context, "error", f"❌ Validation failed: {validation_errors}")
            context.should_stop = True
        else:
            self.log_stage(context, "debug", f"✅ Message validation passed for {context.message.name}")

class SessionResolutionStage(ProcessingStage):
    """Finds existing session by app_id and session_id."""
    
    def __init__(self):
        super().__init__("SESSION_RESOLUTION")
    
    def execute(self, context: MessageProcessingContext) -> None:
        """Find existing session by app_id and session_id."""
        self.log_stage(context, "debug", f"✅ Looking up session {context.session_id} for app_id {context.app_id}")
        
        # Get session from sessions collection
        # This logic was in the original stage_get_session method
        app_id = context.app_id
        session_id = context.session_id
        
        try:
            # Access sessions through the pipeline - we need to get it from the pipeline instance
            # For now, we'll add sessions to context in the main pipeline
            sessions = getattr(context, 'sessions', None)
            if not sessions:
                self.log_stage(context, "error", "❌ Sessions collection not available in context")
                context.session = None
                context.session_found = False
                context.session_active = False
                return
                
            session = sessions.get_session_by_id(app_id, session_id)
            
            if session:
                context.session = session
                context.session_found = True
                
                # Determine session state
                if session.active:
                    context.session_active = True
                    self.log_stage(context, "debug", f"✅ Session found and active: {session_id}")
                elif session.start_time and not session.active:
                    context.session_active = False
                    self.log_stage(context, "debug", f"✅ Session found with start time but not active: {session_id}")
                else:
                    context.session_active = False
                    self.log_stage(context, "debug", f"✅ Session found but not active: {session_id}")
                
                # Additional session state logging for debugging
                self.log_stage(context, "debug", f"📊 Session state - active: {session.active}, ended: {session.ended}, error: {session.error}")
                
            else:
                context.session = None
                context.session_found = False
                context.session_active = False
                self.log_stage(context, "debug", f"✅ Session not found: {session_id}")
                
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error during session resolution: {e}")
            context.session = None
            context.session_found = False
            context.session_active = False
            # Don't set should_stop here - let other stages handle missing session

class SubscriberResolutionStage(ProcessingStage):
    """Finds or creates subscriber based on message data."""
    
    def __init__(self):
        super().__init__("SUBSCRIBER_RESOLUTION")
    
    def execute(self, context: MessageProcessingContext) -> None:
        """Find or create subscriber based on message data."""
        self.log_stage(context, "debug", f"✅ Resolving subscriber")
        
        # Get collections from context
        subscribers = getattr(context, 'subscribers', None)
        sessions = getattr(context, 'sessions', None)
        
        if not subscribers:
            self.log_stage(context, "error", "❌ Subscribers collection not available in context")
            context.subscriber = None
            context.subscriber_found = False
            context.subscriber_created = False
            return
        
        subscriber = None
        resolution_method = None
        
        try:
            # Method 0: Check if we already have a session with a subscriber (HIGHEST PRIORITY)
            if context.session and context.session.subscriber:
                subscriber = context.session.subscriber
                resolution_method = "EXISTING_SESSION"
                self.log_stage(context, "debug", f"✅ Subscriber found from existing session: {subscriber.msisdn}")
            
            # Method 1: Try to find subscriber by MSISDN
            if not subscriber and context.msisdn:
                self.log_stage(context, "debug", f"🔍 Resolving subscriber by MSISDN: {context.msisdn}")
                subscriber = subscribers.get_subscriber_by_msisdn(context.msisdn)
                if subscriber:
                    resolution_method = "MSISDN"
                    self.log_stage(context, "debug", f"✅ Subscriber found by MSISDN: {context.msisdn}")
            
            # Method 2: Try to find subscriber by IMSI
            if not subscriber and context.imsi:
                self.log_stage(context, "debug", f"🔍 Resolving subscriber by IMSI: {context.imsi}")
                subscriber = subscribers.get_subscriber_by_imsi(context.imsi)
                if subscriber:
                    resolution_method = "IMSI"
                    self.log_stage(context, "debug", f"✅ Subscriber found by IMSI: {context.imsi}")
            
            # Method 3: Try to find subscriber by framed IP address (via Gx session)
            if not subscriber and context.framed_ip_address and sessions:
                self.log_stage(context, "debug", f"🔍 Resolving subscriber by framed IP address: {context.framed_ip_address}")
                gx_session = sessions.get_session_by_framed_ip(APP_3GPP_GX, context.framed_ip_address)
                if gx_session and gx_session.subscriber:
                    subscriber = gx_session.subscriber
                    resolution_method = "FRAMED_IP"
                    self.log_stage(context, "debug", f"✅ Subscriber found by framed IP address: {context.framed_ip_address}")
            
            # Method 4: Create new subscriber if none found
            if not subscriber:
                self.log_stage(context, "debug", f"🔍 No subscriber found. Creating new subscriber.")
                subscriber = self._create_subscriber(context, subscribers)
                if subscriber:
                    resolution_method = "CREATED"
                    self.log_stage(context, "debug", f"✅ New subscriber created: {subscriber.msisdn}")
            
            # Set context results
            context.subscriber = subscriber
            context.subscriber_found = subscriber is not None
            context.subscriber_created = (resolution_method == "CREATED")
            context.subscriber_resolution_method = resolution_method
            
            if subscriber:
                self.log_stage(context, "debug", f"📊 Subscriber resolved via {resolution_method}: MSISDN={subscriber.msisdn}, IMSI={getattr(subscriber, 'imsi', 'N/A')}")
            else:
                self.log_stage(context, "warning", f"⚠️ Failed to resolve or create subscriber")
                
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error during subscriber resolution: {e}")
            context.subscriber = None
            context.subscriber_found = False
            context.subscriber_created = False
    
    def _create_subscriber(self, context: MessageProcessingContext, subscribers) -> Optional[Subscriber]:
        """Create a new subscriber based on context data."""
        try:
            # Extract MSISDN and IMSI from context
            msisdn = context.msisdn
            imsi = context.imsi
            
            # If we don't have MSISDN or IMSI, we can't create a subscriber
            if not msisdn and not imsi:
                self.log_stage(context, "warning", f"⚠️ Cannot create subscriber: no MSISDN or IMSI available")
                return None
            
            # Create new subscriber
            subscriber = Subscriber(msisdn=msisdn, imsi=imsi)
            
            # Add to subscribers collection
            subscribers.add_subscriber(subscriber)
            
            self.log_stage(context, "debug", f"✅ Subscriber created and added to collection: MSISDN={msisdn}, IMSI={imsi}")
            return subscriber
            
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error creating subscriber: {e}")
            return None

class SessionCreationStage(ProcessingStage):
    """Creates new session if needed."""
    
    def __init__(self):
        super().__init__("SESSION_CREATION")
    
    def execute(self, context: MessageProcessingContext) -> None:
        """Create new session if needed."""
        self.log_stage(context, "debug", f"✅ Creating session if needed")
        
        # Get collections from context
        sessions = getattr(context, 'sessions', None)
        
        if not sessions:
            self.log_stage(context, "error", "❌ Sessions collection not available in context")
            context.session_created = False
            context.session_started = False
            return
        
        # Check if session creation is needed
        if context.session_found:
            self.log_stage(context, "debug", f"📋 Session already exists: {context.session_id}")
            context.session_created = False
            context.session_started = False
            return
        
        # Check if this message should create a session
        if context.message.is_request and context.message.name not in REQUESTS_CREATE_SESSION:
            self.log_stage(context, "debug", f"📋 Message {context.message.name} not in REQUESTS_CREATE_SESSION - no session creation needed")
            context.session_created = False
            context.session_started = False
            return
        
        # Check if we have a subscriber
        if not context.subscriber:
            self.log_stage(context, "warning", f"⚠️ Cannot create session: no subscriber available")
            context.session_created = False
            context.session_started = False
            return
        
        try:
            # Create appropriate session type based on app_id
            session = self._create_session_by_type(context)
            
            if session:
                context.session = session
                context.session_created = True
                
                # Start the session
                self._start_session(context, session)
                
                # Add session to sessions collection
                sessions.add_session(context.app_id, session)
                
                self.log_stage(context, "debug", f"✅ Session created and added to collection: {session.session_id}")
            else:
                context.session_created = False
                context.session_started = False
                
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error during session creation: {e}")
            context.session_created = False
            context.session_started = False
    
    def _create_session_by_type(self, context: MessageProcessingContext) -> Optional[DiameterSession]:
        """Create appropriate session type based on app_id."""
        try:
            app_id = context.app_id
            session_id = context.session_id
            subscriber = context.subscriber
            
            # Extract session-specific attributes
            framed_ip_address = context.framed_ip_address
            framed_ipv6_prefix = context.framed_ipv6_prefix
            called_station_id = context.called_station_id
            sgsn_mcc_mnc = context.sgsn_mcc_mnc
            
            if app_id == APP_3GPP_GX:
                self.log_stage(context, "debug", f"🔧 Creating GxSession: {session_id}")
                session = GxSession(
                    session_id=session_id,
                    framed_ip_address=framed_ip_address,
                    framed_ipv6_prefix=framed_ipv6_prefix,
                    called_station_id=called_station_id,
                    sgsn_mcc_mnc=sgsn_mcc_mnc,
                    subscriber=subscriber
                )
                self.log_stage(context, "debug", f"✅ GxSession created with IP: {framed_ip_address}")
                
            elif app_id == APP_3GPP_RX:
                self.log_stage(context, "debug", f"🔧 Creating RxSession: {session_id}")
                session = RxSession(session_id=session_id, subscriber=subscriber)
                self.log_stage(context, "debug", f"✅ RxSession created")
                
            elif app_id == APP_3GPP_SY:
                self.log_stage(context, "debug", f"🔧 Creating SySession: {session_id}")
                session = SySession(session_id=session_id, subscriber=subscriber)
                self.log_stage(context, "debug", f"✅ SySession created")
                
            else:
                self.log_stage(context, "error", f"❌ Unknown app_id: {app_id}")
                return None
            
            return session
            
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error creating session: {e}")
            return None
    
    def _start_session(self, context: MessageProcessingContext, session: DiameterSession):
        """Start the session with message timestamp."""
        try:
            if context.message.timestamp:
                session.start(context.message.timestamp)
                context.session_started = True
                self.log_stage(context, "debug", f"✅ Session started with timestamp: {context.message.timestamp}")
            else:
                session.start()
                context.session_started = True
                self.log_stage(context, "debug", f"✅ Session started without timestamp")
                
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error starting session: {e}")
            context.session_started = False

class SessionBindingStage(ProcessingStage):
    """Binds Rx/Sy sessions to Gx sessions."""
    
    def __init__(self):
        super().__init__("SESSION_BINDING")
    
    def execute(self, context: MessageProcessingContext) -> None:
        self.log_stage(context, "debug", f"✅ Binding sessions")
        # TODO: Add session binding logic
        pass

class SessionUpdateStage(ProcessingStage):
    """Updates session state based on message."""
    
    def __init__(self):
        super().__init__("SESSION_UPDATE")
    
    def execute(self, context: MessageProcessingContext) -> None:
        self.log_stage(context, "debug", f"✅ Updating session state")
        # TODO: Add session update logic
        pass

class MessageStorageStage(ProcessingStage):
    """Stores message in session and subscriber."""
    
    def __init__(self):
        super().__init__("MESSAGE_STORAGE")
    
    def execute(self, context: MessageProcessingContext) -> None:
        """Store message in session and subscriber."""
        self.log_stage(context, "debug", f"✅ Storing message")
        
        # Get configuration from context
        save_messages_to_session = getattr(context, 'save_messages_to_session', True)
        save_messages_to_subscriber = getattr(context, 'save_messages_to_subscriber', True)
        save_session_ids_to_subscriber = getattr(context, 'save_session_ids_to_subscriber', True)
        
        message_stored = False
        session_id_added = False
        
        try:
            # Store message in session if configured and session exists
            if save_messages_to_session and context.session:
                message_stored = self._store_message_in_session(context)
            
            # Store message in subscriber if configured and subscriber exists
            if save_messages_to_subscriber and context.subscriber:
                message_stored = self._store_message_in_subscriber(context)
            
            # Add session ID to subscriber if configured
            if save_session_ids_to_subscriber and context.subscriber and context.session:
                session_id_added = self._add_session_id_to_subscriber(context)
            
            # Set message.subscriber reference
            if context.subscriber:
                context.message.subscriber = context.subscriber
                self.log_stage(context, "debug", f"✅ Set message.subscriber reference: {context.subscriber.msisdn}")
            
            # Set context results
            context.message_stored = message_stored
            context.session_id_added = session_id_added
            
            self.log_stage(context, "debug", f"📊 Message storage completed - stored: {message_stored}, session_id_added: {session_id_added}")
            
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error during message storage: {e}")
            context.message_stored = False
            context.session_id_added = False
    
    def _store_message_in_session(self, context: MessageProcessingContext) -> bool:
        """Store message in session if not already present."""
        try:
            session = context.session
            message = context.message
            
            if message not in session.messages:
                session.add_message(message)
                self.log_stage(context, "debug", f"✅ Message {message.name} stored in session {session.session_id}")
                return True
            else:
                self.log_stage(context, "debug", f"📋 Message {message.name} already in session {session.session_id} - skipping")
                return False
                
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error storing message in session: {e}")
            return False
    
    def _store_message_in_subscriber(self, context: MessageProcessingContext) -> bool:
        """Store message in subscriber."""
        try:
            subscriber = context.subscriber
            message = context.message
            
            subscriber.add_message(message)
            self.log_stage(context, "debug", f"✅ Message {message.name} stored in subscriber {subscriber.msisdn}")
            return True
            
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error storing message in subscriber: {e}")
            return False
    
    def _add_session_id_to_subscriber(self, context: MessageProcessingContext) -> bool:
        """Add session ID to subscriber tracking."""
        try:
            subscriber = context.subscriber
            session = context.session
            app_id = context.app_id
            session_id = context.session_id
            
            subscriber.add_session_id(app_id, session_id)
            self.log_stage(context, "debug", f"✅ Session ID {session_id} added to subscriber {subscriber.msisdn} for app_id {app_id}")
            return True
            
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error adding session ID to subscriber: {e}")
            return False

class CleanupStage(ProcessingStage):
    """Final cleanup and session termination if needed."""
    
    def __init__(self):
        super().__init__("CLEANUP")
    
    def execute(self, context: MessageProcessingContext) -> None:
        self.log_stage(context, "debug", f"✅ Final cleanup")
        # TODO: Add cleanup logic
        pass

# Timing Decorator
def timing_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        elapsed_microseconds = (end - start) * 1_000_000
        
        # Set processing time on DiameterMessage
        if func.__name__ == 'main_pipeline' and len(args) >= 2:
            context = args[1]
            diameter_message = context.message
            diameter_message.processing_time_microseconds = elapsed_microseconds
        return result
    return wrapper

# Main Pipeline Class
@dataclass
class MessageProcessingPipeline:
    """Clean, stage-based message processing pipeline."""
    
    sessions: Sessions
    subscribers: Subscribers
    clear_sessions_after_termination: bool = False
    save_messages_to_session: bool = True
    save_messages_to_subscriber: bool = True
    save_session_ids_to_subscriber: bool = True
    statistics: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize the processing stages."""
        self.stages = [
            ValidationStage(),           # Validate message and context
            SessionResolutionStage(),    # Find existing session
            SubscriberResolutionStage(), # Find/create subscriber  
            SessionCreationStage(),      # Create new session if needed
            SessionBindingStage(),       # Bind Rx/Sy to Gx sessions
            SessionUpdateStage(),       # Update session state
            MessageStorageStage(),      # Store message in session/subscriber
            CleanupStage()              # Cleanup and finalize
        ]
    
    def __repr__(self):
        return f"MessageProcessingPipeline(clear_sessions_after_termination={self.clear_sessions_after_termination}, save_messages_to_session={self.save_messages_to_session})"
    
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
        
        try:
            for stage in self.stages:
                stage.execute(context)
                
                # Check if processing should stop
                if getattr(context, 'should_stop', False):
                    logger.debug(f"🛑 Pipeline stopped at stage {stage.name}")
                    break
                    
            logger.debug(f"✅ Pipeline processing completed for message {context.message.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Pipeline processing failed for message {context.message.name}: {e}")
            return False
    
    def handle_stage_error(self, stage: ProcessingStage, context: MessageProcessingContext, error: Exception):
        """Handle errors that occur during stage processing."""
        logger.error(f"❌ [{stage.name}] Stage failed: {error}")
        # TODO: Add error recovery logic
        pass