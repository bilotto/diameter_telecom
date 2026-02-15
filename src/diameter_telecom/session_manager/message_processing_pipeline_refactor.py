from dataclasses import dataclass, field
from typing import Optional, List, Any
import logging
import time
import functools
from datetime import datetime

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
        owner = getattr(context, 'owner_key', None)
        if owner:
            prefix = f"[{owner}] [{self.name}] [{context.message.name}]"
        else:
            prefix = f"[{context.app_id}] [{self.name}] [{context.message.name}]"
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
        
        # # Validate app_id is valid
        # valid_app_ids = [APP_3GPP_GX, APP_3GPP_RX, APP_3GPP_SY]
        # if context.app_id not in valid_app_ids:
        #     validation_errors.append(f"Invalid app_id: {context.app_id}")
        #     self.log_stage(context, "error", f"❌ Validation failed: Invalid app_id {context.app_id}")
        #     context.should_stop = True
        #     return
        
        # Check if message should be processed (skip messages from same host)
        # This logic was in the original SessionManager.process_diameter_message
        # try:
        #     owner_app = getattr(context, 'owner_app', None)
        #     if owner_app and hasattr(owner_app, 'node') and hasattr(owner_app.node, 'origin_host'):
        #         owner_origin_host = owner_app.node.origin_host
        #         message_origin_host = context.origin_host
        #         if owner_origin_host and message_origin_host and message_origin_host == owner_origin_host:
        #             self.log_stage(context, "info", f"🔄 Message comes from the host itself. Skipping processing.")
        #             context.should_stop = True
        #             return
        # except Exception as e:
        #     self.log_stage(context, "debug", f"⚠️ Could not check origin host: {e}")
        
        # Classify message flow type based on message name
        context.message_flow_type = self._classify_message_flow(context.message.name)
        self.log_stage(context, "debug", f"📋 Message flow classified as: {context.message_flow_type}")
        
        # # Validate message has required fields for session creation
        # if context.message.is_request and context.message.name not in REQUESTS_CREATE_SESSION:
        #     # This is not an error, but we need to ensure we have a session
        #     self.log_stage(context, "debug", f"📋 Message {context.message.name} not in REQUESTS_CREATE_SESSION - will need existing session")
        
        # Set validation results
        context.validated = True
        context.validation_errors = validation_errors
        
        if validation_errors:
            self.log_stage(context, "error", f"❌ Validation failed: {validation_errors}")
            context.should_stop = True
        else:
            self.log_stage(context, "debug", f"✅ Message validation passed for {context.message.name}")
    
    def _classify_message_flow(self, message_name: str) -> str:
        """Classify the message flow type based on message name."""
        # Check request messages
        if message_name in REQUESTS_CREATE_SESSION:
            return "START"
        elif message_name in REQUESTS_UPDATE_SESSION:
            return "UPDATE"
        elif message_name in REQUESTS_REFRESH_SESSION:
            return "REFRESH"
        elif message_name in REQUESTS_TERMINATE_SESSION:
            return "TERMINATE"
        # Check response messages
        elif message_name in RESPONSES_CREATE_SESSION:
            return "START"
        elif message_name in RESPONSES_UPDATE_SESSION:
            return "UPDATE"
        elif message_name in RESPONSES_REFRESH_SESSION:
            return "REFRESH"
        elif message_name in RESPONSES_TERMINATE_SESSION:
            return "TERMINATE"
        else:
            return "UNKNOWN"

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
                # We can pre set the context.subscriber here too from the session so we can skip the subscriber resolution stage if we have a subscriber from the session
                if session.subscriber:
                    context.subscriber = session.subscriber
                    context.subscriber_found = True
                    context.subscriber_resolution_method = "SESSION"
                    self.log_stage(context, "debug", f"✅ Subscriber found from session: {session.subscriber.msisdn}")
                
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
        
        # Skip if subscriber already found
        if context.subscriber_found:
            self.log_stage(context, "debug", "📋 Subscriber already resolved - skipping")
            return
        
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
            
            # Method 4: Create new subscriber if none found (requests only; answers typically don't carry MSISDN/IMSI)
            if not subscriber:
                self.log_stage(context, "debug", f"🔍 No subscriber found. Creating new subscriber.")
                subscriber = self._create_subscriber(context, subscribers)
                if subscriber:
                    resolution_method = "CREATED"
                    self.log_stage(context, "debug", f"✅ New subscriber created: {subscriber.msisdn}")
            
            # Ensure subscriber is in the collection if found
            if subscriber and resolution_method != "CREATED":
                # Subscriber was found, ensure it's in the collection
                self._ensure_subscriber_in_collection(subscriber, subscribers, resolution_method, context)
            
            # Set context results
            context.subscriber = subscriber
            context.subscriber_found = subscriber is not None
            context.subscriber_created = (resolution_method == "CREATED")
            context.subscriber_resolution_method = resolution_method
            
            if subscriber:
                self.log_stage(context, "debug", f"📊 Subscriber resolved via {resolution_method}: MSISDN={subscriber.msisdn}, IMSI={getattr(subscriber, 'imsi', 'N/A')}")
            elif context.is_request:
                self.log_stage(context, "warning", f"⚠️ Failed to resolve or create subscriber")
            else:
                self.log_stage(context, "debug", f"Subscriber not resolved (answer message, no MSISDN/IMSI - expected)")
                
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error during subscriber resolution: {e}")
            context.subscriber = None
            context.subscriber_found = False
            context.subscriber_created = False
    
    def _ensure_subscriber_in_collection(self, subscriber: Subscriber, subscribers, resolution_method: str, context: MessageProcessingContext):
        """Ensure subscriber is in the subscribers collection."""
        try:
            # Check if subscriber is already in collection by MSISDN or IMSI
            existing_subscriber = None
            if subscriber.msisdn:
                existing_subscriber = subscribers.get_subscriber_by_msisdn(subscriber.msisdn)
            elif subscriber.imsi:
                existing_subscriber = subscribers.get_subscriber_by_imsi(subscriber.imsi)
            
            if existing_subscriber:
                # Subscriber already in collection - use the one from collection
                if existing_subscriber is not subscriber:
                    self.log_stage(context, "debug", f"📋 Subscriber already in collection, using existing instance: {subscriber.msisdn}")
                    # Update context to use the subscriber from collection
                    context.subscriber = existing_subscriber
                else:
                    self.log_stage(context, "debug", f"📋 Subscriber already in collection: {subscriber.msisdn}")
            else:
                # Subscriber not in collection - add it
                subscribers.add_subscriber(subscriber)
                self.log_stage(context, "debug", f"✅ Added found subscriber to collection: MSISDN={subscriber.msisdn}, method={resolution_method}")
                
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error ensuring subscriber in collection: {e}")
    
    def _create_subscriber(self, context: MessageProcessingContext, subscribers) -> Optional[Subscriber]:
        """Create a new subscriber based on context data."""
        try:
            # Extract MSISDN and IMSI from context
            msisdn = context.msisdn
            imsi = context.imsi
            
            # If we don't have MSISDN or IMSI, we can't create a subscriber.
            # Answers (e.g. CCA) typically don't carry MSISDN/IMSI - only log for requests.
            if not msisdn and not imsi:
                if context.is_request:
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
    """Creates new session for START flow messages only."""
    
    def __init__(self):
        super().__init__("SESSION_CREATION")
    
    def execute(self, context: MessageProcessingContext) -> None:
        """Create new session for START flow messages."""
        self.log_stage(context, "debug", f"✅ Creating session if needed")
        
        # Only requests create sessions; answers (CCA) don't carry MSISDN/IMSI and session already exists
        if not context.is_request:
            self.log_stage(context, "debug", f"📋 Answer message - skipping session creation")
            context.session_created = False
            return
        
        # Skip if not a start flow
        if context.message_flow_type != "START":
            self.log_stage(context, "debug", f"📋 Not a start flow - skipping")
            context.session_created = False
            return
        
        # Get collections from context
        sessions = getattr(context, 'sessions', None)
        
        if not sessions:
            self.log_stage(context, "error", "❌ Sessions collection not available in context")
            context.session_created = False
            return
        
        # Check if session creation is needed
        if context.session_found:
            self.log_stage(context, "debug", f"📋 Session already exists: {context.session_id}")
            context.session_created = False
            return
        
        # Check if this message should create a session
        if context.message.is_request and context.message.name not in REQUESTS_CREATE_SESSION:
            self.log_stage(context, "debug", f"📋 Message {context.message.name} not in REQUESTS_CREATE_SESSION - no session creation needed")
            context.session_created = False
            return
        
        # Check if we have a subscriber
        if not context.subscriber:
            self.log_stage(context, "warning", f"⚠️ Cannot create session: no subscriber available")
            context.session_created = False
            return
        
        try:
            # Create appropriate session type based on app_id
            session = self._create_session_by_type(context)
            
            if session:
                context.session = session
                context.session_created = True
                
                # Add session to sessions collection
                sessions.add_session(context.app_id, session)
                
                self.log_stage(context, "debug", f"✅ Session created and added to collection: {session.session_id}")
            else:
                context.session_created = False
                
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error during session creation: {e}")
            context.session_created = False
    
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
                self.log_stage(context, "debug", f"🔧 Creating DiameterSession: {session_id}")
                session = DiameterSession(session_id=session_id, subscriber=subscriber)
                session.app_id = app_id
                self.log_stage(context, "debug", f"✅ DiameterSession created")
            
            return session
            
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error creating session: {e}")
            return None

class SessionStartStage(ProcessingStage):
    """Starts sessions for START flow messages only."""
    
    def __init__(self):
        super().__init__("SESSION_START")
    
    def execute(self, context: MessageProcessingContext) -> None:
        """Start session for START flow messages."""
        self.log_stage(context, "debug", f"✅ Starting session if needed")
        
        # Skip if not a start flow
        if context.message_flow_type != "START":
            self.log_stage(context, "debug", f"📋 Not a start flow - skipping")
            context.session_started = False
            return
        
        # Check if we have a session to start
        if not context.session:
            self.log_stage(context, "debug", f"📋 No session to start")
            context.session_started = False
            return
        
        # Check if session was just created or already exists
        if not context.session_created and not context.session_found:
            self.log_stage(context, "debug", f"📋 No session created or found - skipping start")
            context.session_started = False
            return
        
        try:
            # Start the session with message timestamp
            if context.message.timestamp:
                context.session.start(context.message.timestamp)
                context.session_started = True
                self.log_stage(context, "debug", f"✅ Session started with timestamp: {context.message.timestamp}")
            else:
                context.session.start()
                context.session_started = True
                self.log_stage(context, "debug", f"✅ Session started without timestamp")

            if not context.is_request and context.message.result_code == E_RESULT_CODE_DIAMETER_SUCCESS:
                context.session.activate()
                context.session_active = True
                self.log_stage(context, "debug", f"✅ Session activated by answer with result code 2001")
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error starting session: {e}")
            context.session_started = False

class SessionBindingStage(ProcessingStage):
    """Binds non-Gx sessions (Rx, Sy, Gy, etc.) to Gx sessions."""
    
    def __init__(self):
        super().__init__("SESSION_BINDING")
    
    def execute(self, context: MessageProcessingContext) -> None:
        """Bind non-Gx sessions to Gx sessions using unified binding logic."""
        self.log_stage(context, "debug", f"✅ Binding sessions")
        
        # Check if session binding is enabled
        enable_session_binding = getattr(context, 'enable_session_binding', True)
        if not enable_session_binding:
            self.log_stage(context, "debug", f"📋 Session binding disabled - skipping")
            context.session_bound = False
            context.binding_method = "DISABLED"
            return
        
        # Get collections from context
        sessions = getattr(context, 'sessions', None)
        
        if not sessions:
            self.log_stage(context, "error", "❌ Sessions collection not available in context")
            context.session_bound = False
            context.binding_method = None
            return
        
        # Check if we have a session to bind
        if not context.session:
            self.log_stage(context, "debug", f"📋 No session to bind")
            context.session_bound = False
            context.binding_method = None
            return
        
        # Gx sessions don't need binding
        if context.app_id == APP_3GPP_GX:
            self.log_stage(context, "debug", f"📋 Gx session - no binding needed")
            context.session_bound = False
            context.binding_method = "NONE"
            return
        
        try:
            # Use unified binding method for all non-Gx app_ids
            success = self._bind_to_gx(context, sessions)
            context.session_bound = success
            
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error during session binding: {e}")
            context.session_bound = False
            context.binding_method = None
    
    def _bind_to_gx(self, context: MessageProcessingContext, sessions) -> bool:
        """Unified binding method for all non-Gx sessions (Rx, Sy, Gy, etc.) to Gx sessions.
        
        Binding strategy (in order):
        1. Framed IP address lookup
        2. Subscriber lookup (via session_ids, MSISDN, or IMSI)
        """
        session = context.session
        binding_method = None
        gx_session = None
        
        app_name = self._get_app_name(context.app_id)
        self.log_stage(context, "debug", f"🔗 Binding {app_name} session {session.session_id} to Gx")
        
        # Check if already bound
        if hasattr(session, 'gx_session_id') and session.gx_session_id:
            self.log_stage(context, "debug", f"📋 {app_name} session already bound to Gx session: {session.gx_session_id}")
            context.binding_method = "ALREADY_BOUND"
            return True
        
        # Method 1: Try framed IP address lookup (first priority)
        if context.framed_ip_address:
            self.log_stage(context, "debug", f"🔍 Trying framed IP binding: {context.framed_ip_address}")
            gx_session = sessions.get_session_by_framed_ip(APP_3GPP_GX, context.framed_ip_address)
            if gx_session:
                binding_method = "FRAMED_IP"
                self.log_stage(context, "debug", f"✅ Found Gx session by framed IP address: {gx_session.session_id}")
        
        # Method 2: Try subscriber session_ids lookup
        if not binding_method and context.subscriber:
            self.log_stage(context, "debug", f"🔍 Trying subscriber session IDs binding")
            gx_session_ids = context.subscriber.session_ids.get(APP_3GPP_GX, [])
            if gx_session_ids:
                gx_session_id = gx_session_ids[0]  # Take first Gx session
                gx_session = sessions.get_session_by_id(APP_3GPP_GX, gx_session_id)
                if gx_session:
                    binding_method = "SUBSCRIBER_SESSION_ID"
                    self.log_stage(context, "debug", f"✅ Found Gx session by subscriber session ID: {gx_session.session_id}")
                else:
                    self.log_stage(context, "debug", f"📋 Gx session ID {gx_session_id} not found in sessions")
                    # Clean up invalid session ID
                    context.subscriber.session_ids.pop(APP_3GPP_GX, None)
                    self.log_stage(context, "debug", f"🧹 Cleaned up invalid Gx session ID from subscriber")
        
        # Method 3: Try MSISDN lookup
        if not binding_method and context.msisdn:
            self.log_stage(context, "debug", f"🔍 Trying MSISDN binding: {context.msisdn}")
            gx_session = sessions.get_session_by_msisdn(APP_3GPP_GX, context.msisdn)
            if gx_session:
                binding_method = "MSISDN"
                self.log_stage(context, "debug", f"✅ Found Gx session by MSISDN: {gx_session.session_id}")
        
        # Method 4: Try IMSI lookup
        if not binding_method and context.imsi:
            self.log_stage(context, "debug", f"🔍 Trying IMSI binding: {context.imsi}")
            gx_session = sessions.get_session_by_imsi(APP_3GPP_GX, context.imsi)
            if gx_session:
                binding_method = "IMSI"
                self.log_stage(context, "debug", f"✅ Found Gx session by IMSI: {gx_session.session_id}")
        
        # Perform binding if we found a Gx session
        if binding_method and gx_session:
            # Re-fetch the session to ensure we have the latest instance
            if binding_method == "FRAMED_IP":
                gx_session = sessions.get_session_by_framed_ip(APP_3GPP_GX, context.framed_ip_address)
            elif binding_method == "SUBSCRIBER_SESSION_ID":
                gx_session_ids = context.subscriber.session_ids.get(APP_3GPP_GX, [])
                if gx_session_ids:
                    gx_session = sessions.get_session_by_id(APP_3GPP_GX, gx_session_ids[0])
            elif binding_method == "MSISDN":
                gx_session = sessions.get_session_by_msisdn(APP_3GPP_GX, context.msisdn)
            elif binding_method == "IMSI":
                gx_session = sessions.get_session_by_imsi(APP_3GPP_GX, context.imsi)
            
            if gx_session:
                # Bind session to Gx
                session.gx_session_id = gx_session.session_id
                session.subscriber = gx_session.subscriber
                
                # Bind Gx to this session
                gx_session.add_bound_session(context.app_id, session.session_id)
                session.add_bound_session(APP_3GPP_GX, gx_session.session_id)
                
                context.binding_method = binding_method
                self.log_stage(context, "info", f"✅ [BINDING] {app_name}Session {session.session_id} bound to GxSession {gx_session.session_id} via {binding_method}")
                return True
        
        # Binding failed
        self.log_stage(context, "warning", f"⚠️ [BINDING] {app_name}Session {session.session_id} not bound to GxSession")
        context.binding_method = "FAILED"
        return False
    
    def _get_app_name(self, app_id: int) -> str:
        """Get application name for logging purposes."""
        if app_id == APP_3GPP_RX:
            return "Rx"
        elif app_id == APP_3GPP_SY:
            return "Sy"
        elif app_id == APP_DIAMETER_CREDIT_CONTROL_APPLICATION:
            return "Gy"
        else:
            return f"App{app_id}"

class SessionRefreshStage(ProcessingStage):
    """Handles session refresh/re-auth operations."""
    
    def __init__(self):
        super().__init__("SESSION_REFRESH")
    
    def execute(self, context: MessageProcessingContext) -> None:
        """Handle session refresh operations (RAR, ASR)."""
        self.log_stage(context, "debug", f"✅ Refreshing session state")
        
        # Skip if no session found
        if not context.session:
            self.log_stage(context, "debug", f"📋 No session to refresh")
            context.session_refreshed = False
            return
        
        # Skip if not a refresh flow
        if context.message_flow_type != "REFRESH":
            self.log_stage(context, "debug", f"📋 Not a refresh flow - skipping")
            context.session_refreshed = False
            return
        
        try:
            # Update session activity time
            context.session.last_activity_time = datetime.now()
            
            # Handle specific refresh operations based on message type
            if context.message.name == "RAR":
                self._handle_rar_refresh(context)
            elif context.message.name == "ASR":
                self._handle_asr_refresh(context)
            
            context.session_refreshed = True
            self.log_stage(context, "debug", f"✅ Session refresh completed: {context.session_id}")
            
        except Exception as e:
            self.log_stage(context, "error", f"❌ Session refresh failed: {e}")
            context.session_refreshed = False
    
    def _handle_rar_refresh(self, context: MessageProcessingContext):
        """Handle Re-Auth-Request refresh."""
        self.log_stage(context, "debug", f"🔄 Processing RAR refresh for session {context.session_id}")
        # RAR-specific refresh logic can be added here
        
    def _handle_asr_refresh(self, context: MessageProcessingContext):
        """Handle Abort-Session-Request refresh."""
        self.log_stage(context, "debug", f"🔄 Processing ASR refresh for session {context.session_id}")
        # ASR-specific refresh logic can be added here

class SessionTerminateStage(ProcessingStage):
    """Handles session termination operations."""
    
    def __init__(self):
        super().__init__("SESSION_TERMINATE")
    
    def execute(self, context: MessageProcessingContext) -> None:
        """Handle session termination operations (CCR-T, STR)."""
        self.log_stage(context, "debug", f"✅ Terminating session")
        
        # Skip if no session found
        if not context.session:
            self.log_stage(context, "debug", f"📋 No session to terminate")
            context.session_terminated = False
            return
         
        # Skip if not a terminate flow
        if context.message_flow_type != "TERMINATE":
            self.log_stage(context, "debug", f"📋 Not a terminate flow - skipping")
            context.session_terminated = False
            return
        
        try:
            # Handle specific termination operations based on message type
            if context.message.name == "CCR-T":
                self._handle_ccr_t_termination(context)
            elif context.message.name == "STR":
                self._handle_str_termination(context)
            
            context.session_terminated = True
            context.session.end(context.message.timestamp)
            if context.clear_sessions_after_termination:
                context.sessions.remove_session(context.app_id, context.session_id)
            self.log_stage(context, "debug", f"✅ Session termination completed: {context.session_id}")
            
        except Exception as e:
            self.log_stage(context, "error", f"❌ Session termination failed: {e}")
            context.session_terminated = False
    
    def _handle_ccr_t_termination(self, context: MessageProcessingContext):
        """Handle CCR-T termination."""
        self.log_stage(context, "debug", f"🔄 Processing CCR-T termination for session {context.session_id}")
        # CCR-T specific termination logic can be added here
        
    def _handle_str_termination(self, context: MessageProcessingContext):
        """Handle STR termination."""
        self.log_stage(context, "debug", f"🔄 Processing STR termination for session {context.session_id}")
        # STR specific termination logic can be added here

class SessionUpdateStage(ProcessingStage):
    """Updates session state for UPDATE flow messages only."""
    
    def __init__(self):
        super().__init__("SESSION_UPDATE")
    
    def execute(self, context: MessageProcessingContext) -> None:
        """Update session state for UPDATE flow messages."""
        self.log_stage(context, "debug", f"✅ Updating session state")
        
        # Skip if no session found
        if not context.session:
            self.log_stage(context, "debug", f"📋 No session to update")
            context.session_updated = False
            return
        
        # Skip if not an update flow
        if context.message_flow_type != "UPDATE":
            self.log_stage(context, "debug", f"📋 Not an update flow - skipping")
            context.session_updated = False
            return
        
        session = context.session
        message = context.message
        session_updated = False
        
        try:
            if message.is_request:
                # Handle request messages - update session attributes
                session_updated = self._handle_request_message(context, session, message)
            else:
                # Handle response messages - activate session, handle errors
                session_updated = self._handle_response_message(context, session, message)
            
            context.session_updated = session_updated
            
            if session_updated:
                self.log_stage(context, "debug", f"✅ Session state updated: active={session.active}, ended={session.ended}, error={session.error}")
            else:
                self.log_stage(context, "debug", f"📋 No session state changes needed")
                
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error during session update: {e}")
            context.session_updated = False
    
    def _handle_request_message(self, context: MessageProcessingContext, session: DiameterSession, message: DiameterMessage) -> bool:
        """Handle request messages - update session attributes."""
        updated = False
        
        try:
            # Update session attributes from request message
            if hasattr(message.message, 'cc_request_number') and message.message.cc_request_number is not None:
                if hasattr(session, 'cc_request_number'):
                    session.cc_request_number = message.message.cc_request_number
                    updated = True
                    self.log_stage(context, "debug", f"📝 Updated cc_request_number: {message.message.cc_request_number}")
            
            # Update SGSN MCC/MNC if present
            if hasattr(message.message, 'sgsn_mcc_mnc') and message.message.sgsn_mcc_mnc:
                if hasattr(session, 'sgsn_mcc_mnc'):
                    session.sgsn_mcc_mnc = message.message.sgsn_mcc_mnc
                    updated = True
                    self.log_stage(context, "debug", f"📝 Updated sgsn_mcc_mnc: {message.message.sgsn_mcc_mnc}")
            
            # Update framed IP address if present and not already set
            if hasattr(message.message, 'framed_ip_address') and message.message.framed_ip_address:
                if hasattr(session, 'framed_ip_address') and not session.framed_ip_address:
                    session.framed_ip_address = message.message.framed_ip_address
                    updated = True
                    self.log_stage(context, "debug", f"📝 Updated framed_ip_address: {message.message.framed_ip_address}")
            
            # Update framed IPv6 prefix if present and not already set
            if hasattr(message.message, 'framed_ipv6_prefix') and message.message.framed_ipv6_prefix:
                if hasattr(session, 'framed_ipv6_prefix') and not session.framed_ipv6_prefix:
                    session.framed_ipv6_prefix = message.message.framed_ipv6_prefix
                    updated = True
                    self.log_stage(context, "debug", f"📝 Updated framed_ipv6_prefix: {message.message.framed_ipv6_prefix}")
            
            # Update called station ID if present and not already set
            if hasattr(message.message, 'called_station_id') and message.message.called_station_id:
                if hasattr(session, 'called_station_id') and not session.called_station_id:
                    session.called_station_id = message.message.called_station_id
                    updated = True
                    self.log_stage(context, "debug", f"📝 Updated called_station_id: {message.message.called_station_id}")
            
            return updated
            
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error handling request message: {e}")
            return False
    
    def _handle_response_message(self, context: MessageProcessingContext, session: DiameterSession, message: DiameterMessage) -> bool:
        """Handle response messages - activate session, update timestamps, etc."""
        updated = False
        
        try:
            # Activate session if it has start_time but is not active (CCA-I success case)
            if session.start_time and not session.active and context.result_code == E_RESULT_CODE_DIAMETER_SUCCESS:
                session.activate()
                updated = True
                self.log_stage(context, "debug", f"✅ Session activated after successful response: {session.session_id}")
            
            # Note: Error handling is now done in the dedicated ErrorHandlingStage
            
            # Update session timestamps
            if message.timestamp:
                if hasattr(session, 'last_activity_time'):
                    session.last_activity_time = message.timestamp
                    updated = True
                    self.log_stage(context, "debug", f"📝 Updated last_activity_time: {message.timestamp}")
            
            return updated
            
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error handling response message: {e}")
            return False

class ErrorHandlingStage(ProcessingStage):
    """Handles error detection and marking sessions with errors."""
    
    def __init__(self):
        super().__init__("ERROR_HANDLING")
    
    def execute(self, context: MessageProcessingContext) -> None:
        """Detect and handle error responses for all message types."""
        self.log_stage(context, "debug", f"✅ Checking for errors")
        
        # Skip if this is a request message
        if context.is_request:
            self.log_stage(context, "debug", f"📋 Request message - skipping error handling")
            context.error_handled = False
            return
        
        # Skip if no session found
        if not context.session:
            self.log_stage(context, "debug", f"📋 No session to mark as error")
            context.error_handled = False
            return
        
        try:
            # Check for error result codes
            if context.result_code and context.result_code != E_RESULT_CODE_DIAMETER_SUCCESS:
                context.session.error = True
                context.error_handled = True
                # self.log_stage(context, "error", f"❌ Session marked as error due to result code: {context.result_code} in message {context.message.name}")
            else:
                context.error_handled = False
                self.log_stage(context, "debug", f"✅ No errors detected in response")
        
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error during error handling: {e}")
            context.error_handled = False

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
                self.log_stage(context, "debug", f"✅ Message {message.name},{message.time} stored in session {session.session_id}")
                return True
            else:
                self.log_stage(context, "debug", f"📋 Message {message.name},{message.time} already in session {session.session_id} - skipping")
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
            self.log_stage(context, "debug", f"✅ Message {message.name},{message.time} stored in subscriber {subscriber.msisdn}")
            return True
            
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error storing message in subscriber: {e}")
            return False
    
    def _add_session_id_to_subscriber(self, context: MessageProcessingContext) -> bool:
        """Add session ID to subscriber tracking if not already present."""
        try:
            subscriber = context.subscriber
            session = context.session
            app_id = context.app_id
            session_id = context.session_id
            
            # Check if session ID is already tracked for this app_id
            existing_session_ids = subscriber.session_ids.get(app_id, [])
            if session_id in existing_session_ids:
                self.log_stage(context, "debug", f"📋 Session ID {session_id} already tracked for subscriber {subscriber.msisdn} for app_id {app_id} - skipping")
                return False
            
            # Only add if it's a new session or if we're creating/starting a session
            if context.session_created or context.session_started:
                subscriber.add_session_id(app_id, session_id)
                self.log_stage(context, "debug", f"✅ Session ID {session_id} added to subscriber {subscriber.msisdn} for app_id {app_id}")
                return True
            else:
                self.log_stage(context, "debug", f"📋 Session not created/started - skipping session ID addition for {session_id}")
                return False
            
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
    save_messages_to_subscriber: bool = False
    save_session_ids_to_subscriber: bool = False
    enable_session_binding: bool = True
    statistics: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize the processing stages."""
        self.stages = {
            'VALIDATION': ValidationStage(),           # Validate message and context
            'SESSION_RESOLUTION': SessionResolutionStage(),    # Find existing session
            'SUBSCRIBER_RESOLUTION': SubscriberResolutionStage(), # Find/create subscriber  
            'SESSION_CREATION': SessionCreationStage(),      # Create new session for START flow
            'SESSION_START': SessionStartStage(),         # Start session for START flow
            'SESSION_BINDING': SessionBindingStage(),       # Bind Rx/Sy to Gx sessions
            'SESSION_REFRESH': SessionRefreshStage(),       # Handle REFRESH flow (RAR, ASR)
            'SESSION_TERMINATE': SessionTerminateStage(),     # Handle TERMINATE flow (CCR-T, STR)
            'SESSION_UPDATE': SessionUpdateStage(),       # Update session for UPDATE flow
            'ERROR_HANDLING': ErrorHandlingStage(),        # Handle error responses for all messages
            'MESSAGE_STORAGE': MessageStorageStage(),      # Store message in session/subscriber
            'CLEANUP': CleanupStage()              # Cleanup and finalize
        }
    
    def __repr__(self):
        return f"MessageProcessingPipeline(clear_sessions_after_termination={self.clear_sessions_after_termination}, save_messages_to_session={self.save_messages_to_session}, enable_session_binding={self.enable_session_binding})"
    
    @timing_decorator
    def main_pipeline(self, context: MessageProcessingContext) -> bool:
        """Main entry point for message processing."""
        logger.debug(f"🚀 Starting pipeline processing for message {context.message.name}")
        
        # Add collections to context so stages can access them
        # todo: Check if this should be here
        context.sessions = self.sessions
        context.subscribers = self.subscribers
        context.clear_sessions_after_termination = self.clear_sessions_after_termination
        context.save_messages_to_session = self.save_messages_to_session
        context.save_messages_to_subscriber = self.save_messages_to_subscriber
        context.save_session_ids_to_subscriber = self.save_session_ids_to_subscriber
        context.enable_session_binding = self.enable_session_binding
        
        try:
            # Always run validation first
            self.stages['VALIDATION'].execute(context)
            if getattr(context, 'should_stop', False):
                logger.debug(f"🛑 Pipeline stopped at ValidationStage")
                return True
            
            # Always run session resolution second
            self.stages['SESSION_RESOLUTION'].execute(context)
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
            self.stages['SUBSCRIBER_RESOLUTION'].execute(context)
        else:
            logger.debug(f"🎯 Smart routing: Skipping SubscriberResolutionStage - subscriber already found")

        if context.message_flow_type == "START":
            # New session flow
            if not context.session_found:
                logger.debug(f"🎯 Smart routing: START flow - creating session")
                self.stages['SESSION_CREATION'].execute(context)
            else:
                logger.debug(f"🎯 Smart routing: START flow but session exists")
            #
            self.stages['SESSION_START'].execute(context)
            self.stages['SESSION_BINDING'].execute(context)

        elif context.message_flow_type == "UPDATE":
            # Update session flow
            if context.session_found:
                logger.debug(f"🎯 Smart routing: UPDATE flow - updating session")
                self.stages['SESSION_UPDATE'].execute(context)
            else:
                logger.debug(f"🎯 Smart routing: UPDATE flow but no session - skipping update")

        elif context.message_flow_type == "REFRESH":
            # Refresh session flow
            if context.session_found:
                logger.debug(f"🎯 Smart routing: REFRESH flow - refreshing session")
                self.stages['SESSION_REFRESH'].execute(context)
            else:
                logger.debug(f"🎯 Smart routing: REFRESH flow but no session - skipping refresh")

        elif context.message_flow_type == "TERMINATE":
            # Terminate session flow
            if context.session_found:
                logger.debug(f"🎯 Smart routing: TERMINATE flow - terminating session")
                self.stages['SESSION_TERMINATE'].execute(context)
            else:
                logger.debug(f"🎯 Smart routing: TERMINATE flow but no session - skipping termination")
        else:
            # Unknown flow type
            logger.debug(f"🎯 Smart routing: Unknown flow type {context.message_flow_type} - updating session if available")
            if context.session_found:
                self.stages['SESSION_UPDATE'].execute(context)
        
        # Always run error handling for response messages (regardless of flow type)
        self.stages['ERROR_HANDLING'].execute(context)
        
        # Always run message storage and cleanup
        self.stages['MESSAGE_STORAGE'].execute(context)
        self.stages['CLEANUP'].execute(context)
    
    def handle_stage_error(self, stage: ProcessingStage, context: MessageProcessingContext, error: Exception):
        """Handle errors that occur during stage processing."""
        logger.error(f"❌ [{stage.name}] Stage failed: {error}")
        # TODO: Add error recovery logic
        pass