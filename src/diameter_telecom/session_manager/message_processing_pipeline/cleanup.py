from .base import ProcessingStage
from .constants import *
from ..message_processing_context import MessageProcessingContext


class CleanupStage(ProcessingStage):
    """Final cleanup and session termination if needed."""
    
    def __init__(self):
        super().__init__(STAGE_CLEANUP)
    
    def execute(self, context: MessageProcessingContext) -> None:
        """Perform final cleanup operations."""
        self.log_stage(context, "debug", f"✅ Final cleanup")
        # TODO: Add cleanup logic if needed
        pass
