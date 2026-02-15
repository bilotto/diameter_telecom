from .base import ProcessingStage
from .constants import *
from ..message_processing_context import MessageProcessingContext
from ...session._diameter_session import DiameterSession
from ...message import DiameterMessage
from ...constants import E_RESULT_CODE_DIAMETER_SUCCESS


class SessionUpdateStage(ProcessingStage):
    """Updates session state for UPDATE flow messages only."""
    
    def __init__(self):
        super().__init__(STAGE_SESSION_UPDATE)
    
    def execute(self, context: MessageProcessingContext) -> None:
        """Update session state for UPDATE flow messages."""
        self.log_stage(context, "debug", f"✅ Updating session state")
        
        # Skip if no session found
        if not context.session:
            self.log_stage(context, "debug", f"📋 No session to update")
            context.session_updated = False
            return
        
        # Skip if not an update flow
        if context.message_flow_type != FLOW_UPDATE:
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
