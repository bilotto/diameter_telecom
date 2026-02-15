from .base import ProcessingStage
from ..message_processing_context import MessageProcessingContext


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
