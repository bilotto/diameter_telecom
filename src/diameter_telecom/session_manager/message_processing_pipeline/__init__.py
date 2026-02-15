"""
Message Processing Pipeline Module

This module contains a clean, stage-based pipeline for processing Diameter messages.
Each stage is isolated in its own file for better maintainability and clarity.

Main Components:
    - MessageProcessingPipeline: Main pipeline orchestrator
    - ProcessingStage: Base class for all stages
    - Individual stage implementations for validation, session lifecycle, etc.

Usage:
    from diameter_telecom.session_manager.message_processing_pipeline import MessageProcessingPipeline
    
    pipeline = MessageProcessingPipeline(sessions, subscribers)
    pipeline.main_pipeline(context)
"""

# Base classes
from .base import ProcessingStage
from .decorators import timing_decorator

# Pipeline orchestrator
from .pipeline import MessageProcessingPipeline

# Individual stage implementations
from .validation import ValidationStage
from .session_resolution import SessionResolutionStage
from .subscriber_resolution import SubscriberResolutionStage
from .session_creation import SessionCreationStage
from .session_start import SessionStartStage
from .session_binding import SessionBindingStage
from .session_refresh import SessionRefreshStage
from .session_terminate import SessionTerminateStage
from .session_update import SessionUpdateStage
from .error_handling import ErrorHandlingStage
from .message_storage import MessageStorageStage
from .cleanup import CleanupStage

__all__ = [
    # Base classes
    'ProcessingStage',
    'timing_decorator',
    
    # Main pipeline
    'MessageProcessingPipeline',
    
    # Individual stages
    'ValidationStage',
    'SessionResolutionStage',
    'SubscriberResolutionStage',
    'SessionCreationStage',
    'SessionStartStage',
    'SessionBindingStage',
    'SessionRefreshStage',
    'SessionTerminateStage',
    'SessionUpdateStage',
    'ErrorHandlingStage',
    'MessageStorageStage',
    'CleanupStage',
]
