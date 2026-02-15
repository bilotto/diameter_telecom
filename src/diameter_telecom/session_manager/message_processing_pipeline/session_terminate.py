from .base import ProcessingStage
from ..message_processing_context import MessageProcessingContext


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
