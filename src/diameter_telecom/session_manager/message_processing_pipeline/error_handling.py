from .base import ProcessingStage
from ..message_processing_context import MessageProcessingContext
from ...constants import E_RESULT_CODE_DIAMETER_SUCCESS


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
