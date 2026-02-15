from .base import ProcessingStage
from .constants import *
from ..message_processing_context import MessageProcessingContext
from ...constants import E_RESULT_CODE_DIAMETER_SUCCESS


class SessionStartStage(ProcessingStage):
    """Starts sessions for START flow messages only."""
    
    def __init__(self):
        super().__init__(STAGE_SESSION_START)
    
    def execute(self, context: MessageProcessingContext) -> None:
        """Start session for START flow messages."""
        self.log_stage(context, "debug", f"✅ Starting session if needed")
        
        # Skip if not a start flow
        if context.message_flow_type != FLOW_START:
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
