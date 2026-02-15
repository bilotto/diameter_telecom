from .base import ProcessingStage
from .constants import *
from ..message_processing_context import MessageProcessingContext
from ...constants import *


class SessionBindingStage(ProcessingStage):
    """Binds non-Gx sessions (Rx, Sy, Gy, etc.) to Gx sessions."""
    
    def __init__(self):
        super().__init__(STAGE_SESSION_BINDING)
    
    def execute(self, context: MessageProcessingContext) -> None:
        """Bind non-Gx sessions to Gx sessions using unified binding logic."""
        self.log_stage(context, "debug", f"✅ Binding sessions")
        
        # Check if session binding is enabled
        enable_session_binding = getattr(context, 'enable_session_binding', True)
        if not enable_session_binding:
            self.log_stage(context, "debug", f"📋 Session binding disabled - skipping")
            context.session_bound = False
            context.binding_method = BINDING_DISABLED
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
            context.binding_method = BINDING_NONE
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
            context.binding_method = BINDING_ALREADY_BOUND
            return True
        
        # Method 1: Try framed IP address lookup (first priority)
        if context.framed_ip_address:
            self.log_stage(context, "debug", f"🔍 Trying framed IP binding: {context.framed_ip_address}")
            gx_session = sessions.get_session_by_framed_ip(APP_3GPP_GX, context.framed_ip_address)
            if gx_session:
                binding_method = BINDING_FRAMED_IP
                self.log_stage(context, "debug", f"✅ Found Gx session by framed IP address: {gx_session.session_id}")
        
        # Method 2: Try subscriber session_ids lookup
        if not binding_method and context.subscriber:
            self.log_stage(context, "debug", f"🔍 Trying subscriber session IDs binding")
            gx_session_ids = context.subscriber.session_ids.get(APP_3GPP_GX, [])
            if gx_session_ids:
                gx_session_id = gx_session_ids[0]  # Take first Gx session
                gx_session = sessions.get_session_by_id(APP_3GPP_GX, gx_session_id)
                if gx_session:
                    binding_method = BINDING_SUBSCRIBER_SESSION_ID
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
                binding_method = BINDING_MSISDN
                self.log_stage(context, "debug", f"✅ Found Gx session by MSISDN: {gx_session.session_id}")
        
        # Method 4: Try IMSI lookup
        if not binding_method and context.imsi:
            self.log_stage(context, "debug", f"🔍 Trying IMSI binding: {context.imsi}")
            gx_session = sessions.get_session_by_imsi(APP_3GPP_GX, context.imsi)
            if gx_session:
                binding_method = BINDING_IMSI
                self.log_stage(context, "debug", f"✅ Found Gx session by IMSI: {gx_session.session_id}")
        
        # Perform binding if we found a Gx session
        if binding_method and gx_session:
            # Re-fetch the session to ensure we have the latest instance
            if binding_method == BINDING_FRAMED_IP:
                gx_session = sessions.get_session_by_framed_ip(APP_3GPP_GX, context.framed_ip_address)
            elif binding_method == BINDING_SUBSCRIBER_SESSION_ID:
                gx_session_ids = context.subscriber.session_ids.get(APP_3GPP_GX, [])
                if gx_session_ids:
                    gx_session = sessions.get_session_by_id(APP_3GPP_GX, gx_session_ids[0])
            elif binding_method == BINDING_MSISDN:
                gx_session = sessions.get_session_by_msisdn(APP_3GPP_GX, context.msisdn)
            elif binding_method == BINDING_IMSI:
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
        context.binding_method = BINDING_FAILED
        return False
    
    def _get_app_name(self, app_id: int) -> str:
        """Get application name for logging purposes."""
        if app_id == APP_3GPP_RX:
            return APP_NAME_RX
        elif app_id == APP_3GPP_SY:
            return APP_NAME_SY
        elif app_id == APP_DIAMETER_CREDIT_CONTROL_APPLICATION:
            return APP_NAME_GY
        else:
            return f"App{app_id}"
