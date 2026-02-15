from datetime import datetime
from .base import ProcessingStage
from .constants import *
from ..message_processing_context import MessageProcessingContext


class SessionRefreshStage(ProcessingStage):
    """Handles session refresh/re-auth operations."""
    
    def __init__(self):
        super().__init__(STAGE_SESSION_REFRESH)
    
    def execute(self, context: MessageProcessingContext) -> None:
        """Handle session refresh operations (RAR, ASR)."""
        self.log_stage(context, "debug", f"✅ Refreshing session state")
        
        # Skip if no session found
        if not context.session:
            self.log_stage(context, "debug", f"📋 No session to refresh")
            context.session_refreshed = False
            return
        
        # Skip if not a refresh flow
        if context.message_flow_type != FLOW_REFRESH:
            self.log_stage(context, "debug", f"📋 Not a refresh flow - skipping")
            context.session_refreshed = False
            return
        
        try:
            # Update session activity time
            context.session.last_activity_time = datetime.now()
            
            # Handle specific refresh operations based on message type
            if context.message.name == MSG_RAR:
                self._handle_rar_refresh(context)
            elif context.message.name == MSG_ASR:
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
