from ..subscriber import Subscriber, Subscribers
from ..session import GxSession, RxSession, SySession, DiameterSession
from .sessions import Sessions
from .message_processing_pipeline import MessageProcessingPipeline
from .message_processing_context import MessageProcessingContext
from ..csv_file import CsvFile
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
import threading
import time
import logging
from ..constants import *
from ..diameter_layer.parse_avp import *
from ..message import DiameterMessage
from contextlib import contextmanager

logger = logging.getLogger(__name__)
import uuid


@dataclass
class SessionManager:
    """Centralized session and subscriber management for Diameter applications.
    
    This class handles high-level orchestration of message processing and maintains
    the data stores for sessions, subscribers, and messages. The actual message 
    processing logic is delegated to MessageProcessingPipeline.
    
    CSV Integration:
    If a csv_file is provided, every processed message will be automatically
    written to the CSV file during processing using smart attribute resolution.
    
    Thread Safety:
    This class is thread-safe and supports true parallel message processing.
    Multiple threads can process different messages simultaneously. Fine-grained
    locks protect shared data structures only when necessary, maximizing throughput
    for high-performance telecom applications.
    """
    sessions: Sessions = field(default_factory=Sessions, repr=False)
    subscribers: Subscribers = field(default_factory=Subscribers, repr=False)
    messages: List[DiameterMessage] = field(default_factory=list, repr=False)
    csv_file: Optional[CsvFile] = field(default=None, repr=False)
    statistics: dict = field(default_factory=dict, repr=False)
    pipeline: MessageProcessingPipeline = field(init=False, repr=False)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8], repr=True)
    
    # Registry of applications using this SessionManager
    owners: Dict[str, Any] = field(default_factory=dict, repr=False)  # key: "ClassName(origin_host)", value: app object

    # Options
    clear_sessions_after_termination: bool = field(default=True, repr=False)
    
    # Thread safety locks
    _sessions_lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)
    _subscribers_lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)
    _messages_lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)
    _csv_lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)
    _owners_lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)

    def __post_init__(self):
        """Initialize the message processing pipeline"""
        self.pipeline = MessageProcessingPipeline(
            sessions=self.sessions,
            subscribers=self.subscribers,
            clear_sessions_after_termination=self.clear_sessions_after_termination,
            statistics=self.statistics,
        )

    def set_subscribers(self, subscribers: Subscribers):
        self.subscribers = subscribers
    
    @contextmanager
    def _sessions_read_lock(self):
        """Context manager for read access to sessions."""
        self._sessions_lock.acquire()
        try:
            yield
        finally:
            self._sessions_lock.release()
    
    @contextmanager
    def _sessions_write_lock(self):
        """Context manager for write access to sessions."""
        self._sessions_lock.acquire()
        try:
            yield
        finally:
            self._sessions_lock.release()
    
    @contextmanager
    def _subscribers_read_lock(self):
        """Context manager for read access to subscribers."""
        self._subscribers_lock.acquire()
        try:
            yield
        finally:
            self._subscribers_lock.release()
    
    @contextmanager
    def _subscribers_write_lock(self):
        """Context manager for write access to subscribers."""
        self._subscribers_lock.acquire()
        try:
            yield
        finally:
            self._subscribers_lock.release()
    
    @contextmanager
    def _messages_lock_context(self):
        """Context manager for access to messages."""
        self._messages_lock.acquire()
        try:
            yield
        finally:
            self._messages_lock.release()
    
    
    @contextmanager
    def _csv_lock_context(self):
        """Context manager for CSV file operations."""
        self._csv_lock.acquire()
        try:
            yield
        finally:
            self._csv_lock.release()
    
    @contextmanager
    def _owners_lock_context(self):
        """Context manager for owners registry operations."""
        self._owners_lock.acquire()
        try:
            yield
        finally:
            self._owners_lock.release()

    # def get_messages(self):
    #     return sorted(self.messages, key=lambda x: x.timestamp if x.timestamp else float('inf'))

    def process_diameter_message(self, dm: DiameterMessage, owner_app: Optional[Any] = None) -> Optional[MessageProcessingContext]:
        """Main entry point for processing Diameter messages.
        
        This method orchestrates the message processing by delegating to the
        MessageProcessingPipeline and handling the final message storage.
        
        Args:
            dm: The Diameter message to process
            owner_app: Optional reference to the application object that processed this message
        
        Returns:
            Optional[MessageProcessingContext]: The processing context containing all processed data,
            or None if the message was filtered out
        """
        context: MessageProcessingContext = MessageProcessingContext.from_diameter_message(dm)
        context.owner_app = owner_app
        
        # Register the owner if provided
        if owner_app:
            self._register_owner(owner_app)
            context.owner = f"{owner_app.__class__.__name__}({owner_app.node.origin_host})"
        else:
            context.owner = "Unknown"
        
        # logger.info(f"Processing {dm.name} - {dm.session_id}")
        logger.info(f"[{context.owner}] Processing {dm.name} - {dm.session_id}")
        result = self.pipeline.main_pipeline(context)
        if not result:
            return None
        # Auto-write to CSV if configured (still needs synchronization for file operations)
        if self.csv_file:
            self._write_context_to_csv(context)
        return context

    def _write_context_to_csv(self, context: MessageProcessingContext):
        """
        Internal method to write context to the configured CSV file.
        
        This method uses the MessageProcessingContext's smart attribute resolution
        to populate CSV columns from DiameterMessage, Session, and Subscriber objects.
        
        Args:
            context: MessageProcessingContext containing all processed data
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Writing context to CSV: {context}")
        try:
            row = {}
            for column in self.csv_file.get_csv_columns():
                value = context.resolve_attribute(column)
                row[column] = value if value else ""
            
            self.csv_file.write_row(row)
            self.csv_file.flush()
            return True
            
        except Exception as e:
            logger.error(f"Error auto-writing to CSV for message {context.message.name if context.message else 'unknown'} - {context.session_id}: {e}")
            return False

    def send_request_with_session_management(self, diameter_message: DiameterMessage, send_request_func, timeout=10) -> DiameterMessage:
        if not diameter_message.timestamp:
            diameter_message.timestamp = time.time()

        request_context = self.process_diameter_message(diameter_message)
        
        answer = send_request_func(diameter_message.message, timeout=timeout)
        diameter_message_answer = DiameterMessage(answer)
        
        answer_context = self.process_diameter_message(diameter_message_answer)

        if answer_context.session and answer_context.session.error:
            self.sessions.remove_session(answer_context.message.app_id, answer_context.session_id)
        
        if diameter_message_answer.result_code != E_RESULT_CODE_DIAMETER_SUCCESS:
            logger.error(f"Answer with error: \n {diameter_message_answer}")
        # logger.info(f"\n{diameter_message_answer.dump()}")

        

        if not diameter_message_answer.timestamp:
        # Set timestamp on answer
            diameter_message_answer.timestamp = time.time()
        
        return diameter_message_answer

    def to_dict(self) -> dict:
        session_manager_dict = {}
        session_manager_dict['id'] = self.id
        return session_manager_dict

    def _get_app_name(self, app_id: int) -> str:
        """Convert application ID to readable name."""
        app_names = {
            16777238: "Gx",  # APP_3GPP_GX
            16777236: "Rx",  # APP_3GPP_RX  
            16777302: "Sy"   # APP_3GPP_SY
        }
        return app_names.get(app_id, f"App_{app_id}")

    def get_session_messages(self, app_id: int, session_id: str) -> List[DiameterMessage]:
        """Get messages for a specific session.
        
        Thread Safety: This method is thread-safe and can be called concurrently
        from multiple threads.
        """
        with self._sessions_read_lock():
            session = self.sessions.get_session_by_id(app_id, session_id)
            if session:
                return session.messages.copy()  # Return a copy to avoid external modification
            return []

    def get_messages_by_msisdn(self, msisdn: str) -> List[DiameterMessage]:
        """Get all messages for a subscriber by MSISDN.
        
        Thread Safety: This method is thread-safe and can be called concurrently
        from multiple threads.
        """
        with self._subscribers_read_lock():
            subscriber = self.subscribers.get_subscriber_by_msisdn(msisdn)
            if not subscriber:
                return []
        
        messages: List[DiameterMessage] = []
        # Get session IDs safely
        session_ids = subscriber.session_ids.copy()  # Copy to avoid modification during iteration
        
        for app_id, session_id_list in session_ids.items():
            for session_id in session_id_list:
                messages.extend(self.get_session_messages(app_id, session_id))
        
        messages.sort(key=lambda x: x.timestamp if x.timestamp else float('inf'))
        return messages

    def get_subscriber_message_by_index(self, msisdn: str, index: int) -> DiameterMessage:
        """Get a specific message by index for a subscriber.
        
        Thread Safety: This method is thread-safe and can be called concurrently
        from multiple threads.
        """
        messages = self.get_messages_by_msisdn(msisdn)
        if 0 <= index < len(messages):
            return messages[index].dump()
        else:
            raise IndexError(f"Message index {index} out of range for subscriber {msisdn}")

    def _calculate_statistics(self, sessions_data: dict, subscribers_data: dict, messages_data: list) -> dict:
        """Calculate comprehensive statistics for the session manager."""
        try:
            stats = {
                "total_sessions": 0,
                "total_subscribers": len(subscribers_data),
                "total_messages": len(messages_data),
                "sessions_by_app": {},
                "sessions_by_status": {"active": 0, "ended": 0, "error": 0},
                "subscribers_with_messages": 0
            }
            
            # Calculate session statistics
            for app_name, app_data in sessions_data.items():
                app_sessions = app_data.get("sessions", {})
                app_total = len(app_sessions)
                stats["total_sessions"] += app_total
                stats["sessions_by_app"][app_name] = {
                    "total": app_total,
                    "active": 0,
                    "ended": 0,
                    "error": 0
                }
                
                for session in app_sessions.values():
                    if session.get("active"):
                        stats["sessions_by_status"]["active"] += 1
                        stats["sessions_by_app"][app_name]["active"] += 1
                    elif session.get("ended"):
                        stats["sessions_by_status"]["ended"] += 1
                        stats["sessions_by_app"][app_name]["ended"] += 1
                    elif session.get("error"):
                        stats["sessions_by_status"]["error"] += 1
                        stats["sessions_by_app"][app_name]["error"] += 1
            
            # Calculate subscriber statistics
            for subscriber in subscribers_data.values():
                if subscriber.get("message_count", 0) > 0:
                    stats["subscribers_with_messages"] += 1
            
            return stats
            
        except Exception as e:
            logger.exception("Failed to calculate session manager statistics")
            return {"error": f"Statistics calculation failed: {str(e)}"}

    def _register_owner(self, owner_app: Any):
        """Register an application as an owner of this SessionManager.
        
        Args:
            owner_app: The application object to register
        """
        if not owner_app:
            return
            
        owner_key = f"{owner_app.__class__.__name__}({owner_app.node.origin_host})"
        
        with self._owners_lock_context():
            self.owners[owner_key] = owner_app
            logger.debug(f"Registered owner: {owner_key}")

    def get_owner(self, owner_key: str) -> Optional[Any]:
        """Get an owner application by its key.
        
        Args:
            owner_key: The owner key in format "ClassName(origin_host)"
            
        Returns:
            The application object if found, None otherwise
        """
        with self._owners_lock_context():
            return self.owners.get(owner_key)

    def get_owners_by_class(self, class_name: str) -> List[Any]:
        """Get all owners of a specific class.
        
        Args:
            class_name: The class name to search for (e.g., "PcrfGxApplication")
            
        Returns:
            List of application objects of the specified class
        """
        with self._owners_lock_context():
            matching_owners = []
            for owner_key, owner_app in self.owners.items():
                if owner_app.__class__.__name__ == class_name:
                    matching_owners.append(owner_app)
            return matching_owners

    def get_owners_by_app_id(self, app_id: int) -> List[Any]:
        """Get all owners with a specific application ID.
        
        Args:
            app_id: The application ID to search for
            
        Returns:
            List of application objects with the specified app_id
        """
        with self._owners_lock_context():
            matching_owners = []
            for owner_key, owner_app in self.owners.items():
                if hasattr(owner_app, 'application_id') and owner_app.application_id == app_id:
                    matching_owners.append(owner_app)
            return matching_owners

    def get_all_owners(self) -> Dict[str, Any]:
        """Get all registered owners.
        
        Returns:
            Dictionary of owner_key -> owner_app mappings
        """
        with self._owners_lock_context():
            return self.owners.copy()

    def remove_owner(self, owner_key: str) -> bool:
        """Remove an owner from the registry.
        
        Args:
            owner_key: The owner key to remove
            
        Returns:
            True if the owner was removed, False if not found
        """
        with self._owners_lock_context():
            if owner_key in self.owners:
                del self.owners[owner_key]
                logger.debug(f"Removed owner: {owner_key}")
                return True
            return False

    def get_owner_count(self) -> int:
        """Get the number of registered owners.
        
        Returns:
            Number of registered owners
        """
        with self._owners_lock_context():
            return len(self.owners)


