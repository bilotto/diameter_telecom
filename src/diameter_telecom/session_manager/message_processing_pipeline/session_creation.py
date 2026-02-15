from typing import Optional
from .base import ProcessingStage
from .constants import *
from ..message_processing_context import MessageProcessingContext
from ...session._diameter_session import DiameterSession
from ...session.gx import GxSession
from ...session.rx import RxSession
from ...session.sy import SySession
from ...constants import *


class SessionCreationStage(ProcessingStage):
    """Creates new session for START flow messages only."""
    
    def __init__(self):
        super().__init__(STAGE_SESSION_CREATION)
    
    def execute(self, context: MessageProcessingContext) -> None:
        """Create new session for START flow messages."""
        self.log_stage(context, "debug", f"✅ Creating session if needed")
        
        # Only requests create sessions; answers (CCA) don't carry MSISDN/IMSI and session already exists
        if not context.is_request:
            self.log_stage(context, "debug", f"📋 Answer message - skipping session creation")
            context.session_created = False
            return
        
        # Skip if not a start flow
        if context.message_flow_type != FLOW_START:
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
