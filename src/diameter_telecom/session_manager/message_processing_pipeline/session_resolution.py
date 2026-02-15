from .base import ProcessingStage
from ..message_processing_context import MessageProcessingContext


class SessionResolutionStage(ProcessingStage):
    """Finds existing session by app_id and session_id."""
    
    def __init__(self):
        super().__init__("SESSION_RESOLUTION")
    
    def execute(self, context: MessageProcessingContext) -> None:
        """Find existing session by app_id and session_id."""
        self.log_stage(context, "debug", f"✅ Looking up session {context.session_id} for app_id {context.app_id}")
        
        # Get session from sessions collection
        app_id = context.app_id
        session_id = context.session_id
        
        try:
            # Access sessions through the context
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
                # Pre-set the subscriber from session if available
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
