from .base import ProcessingStage
from ..message_processing_context import MessageProcessingContext
from ...constants import *


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
        
        # Classify message flow type based on message name
        context.message_flow_type = self._classify_message_flow(context.message.name)
        self.log_stage(context, "debug", f"📋 Message flow classified as: {context.message_flow_type}")
        
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
