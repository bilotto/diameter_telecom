import logging
from ..message_processing_context import MessageProcessingContext

logger = logging.getLogger("diameter_telecom.session_manager")


class ProcessingStage:
    """Base class for all processing stages."""
    
    def __init__(self, name: str):
        self.name = name
    
    def execute(self, context: MessageProcessingContext) -> None:
        """Execute this stage. Override in subclasses."""
        logger.debug(f"🔧 [{self.name}] Stage executed (dummy implementation)")
        pass
    
    def log_stage(self, context: MessageProcessingContext, level: str, message: str):
        """Helper method for consistent stage logging."""
        owner = getattr(context, 'owner_key', None)
        if owner:
            prefix = f"[{owner}] [{self.name}] [{context.message.name}]"
        else:
            prefix = f"[{context.app_id}] [{self.name}] [{context.message.name}]"
        full_message = f"{prefix} {message}"
        
        if level == "debug":
            logger.debug(full_message)
        elif level == "info":
            logger.info(full_message)
        elif level == "warning":
            logger.warning(full_message)
        elif level == "error":
            logger.error(full_message)
