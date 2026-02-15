from ..subscriber import Subscribers
from .sessions import Sessions
from .message_processing_pipeline import MessageProcessingPipeline
from .message_processing_context import MessageProcessingContext
from ..csv_file import CsvFile
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
import threading
import logging
from ..constants import *
from ..diameter_layer.parse_avp import *
from ..message import DiameterMessage
from contextlib import contextmanager

logger = logging.getLogger("diameter_telecom.session_manager")
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
    
    To enable CSV logging, you can either:
    - Set create_csv=True and optionally specify csv_filename (default: "diameter_messages_{id}.csv")
    - Or manually provide a csv_file instance
    
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
    
    # Options
    clear_sessions_after_termination: bool = field(default=True, repr=False)
    enable_session_binding: bool = field(default=True, repr=False)
    create_csv: bool = field(default=False, repr=False)
    csv_filename: Optional[str] = field(default=None, repr=False)
    save_contexts: bool = field(default=False, repr=False)
    csv_flush_every_message: bool = field(default=False, repr=False)
    
    # Thread safety locks
    _sessions_lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)
    _subscribers_lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)
    _messages_lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)
    _csv_lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)
    _owners_lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)
    owners: Dict[str, Any] = field(default_factory=dict, repr=False)
    

    def __post_init__(self):
        """Initialize the message processing pipeline and CSV file if requested"""
        self.pipeline = MessageProcessingPipeline(
            sessions=self.sessions,
            subscribers=self.subscribers,
            clear_sessions_after_termination=self.clear_sessions_after_termination,
            enable_session_binding=self.enable_session_binding,
            statistics=self.statistics,
        )
        
        # Auto-create CSV file if requested
        if self.create_csv and not self.csv_file:
            filename = self.csv_filename or f"diameter_messages_{self.id}.csv"
            self.csv_file = CsvFile(filename)
            logger.info(f"✅ CSV logging enabled: {filename}")

    def set_subscribers(self, subscribers: Subscribers):
        self.subscribers = subscribers
    
    def log_message(self, context: Optional[MessageProcessingContext], level: str, message: str):
        """SessionManager-level logging with owner prefix from context."""
        owner: Optional[str] = None
        try:
            if context and getattr(context, 'owner_key', None):
                owner = context.owner_key
            elif context and getattr(context, 'owner_app', None):
                owner_app = context.owner_app
                origin_host = None
                try:
                    if hasattr(owner_app, 'node') and hasattr(owner_app.node, 'origin_host'):
                        origin_host = owner_app.node.origin_host
                except Exception:
                    origin_host = None
                owner = f"{owner_app.__class__.__name__}({origin_host})" if origin_host else owner_app.__class__.__name__
        except Exception:
            owner = None
        prefix = f"[{owner}] " if owner else ""
        full_message = f"{prefix}{message}"
        if level == "debug":
            logger.debug(full_message)
        elif level == "info":
            logger.info(full_message)
        elif level == "warning":
            logger.warning(full_message)
        elif level == "error":
            logger.error(full_message)
    
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
    
    def process_diameter_message(self, dm: DiameterMessage, owner_app: Optional[Any] = None) -> Optional[MessageProcessingContext]:
        context: MessageProcessingContext = MessageProcessingContext.from_diameter_message(dm)
        context.owner_app = owner_app
        if owner_app is not None:
            try:
                owner_key = self.register_owner(owner_app)
            except Exception:
                owner_key = None
            context.owner_key = owner_key
        result = self.pipeline.main_pipeline(context)
        if not result:
            self.log_message(context, "error", f"❌ Pipeline processing failed for message {context.message.name if context.message else 'unknown'}")
            return None
        # Auto-write to CSV if configured (thread-safe)
        if self.csv_file:
            self._write_context_to_csv(context)
        # if context.result_code and context.result_code != E_RESULT_CODE_DIAMETER_SUCCESS:
        #     self.log_message(context, "error", f"❌ Result code: {context.result_code} for message {context.message.name if context.message else 'unknown'}")
        #     self.log_message(context, "error", f"❌ Message at {context.message.time}:\n{context.message.dump()}")
        #     return None
        return context

    def _write_context_to_csv(self, context: MessageProcessingContext):
        with self._csv_lock_context():
            try:
                row = {}
                for column in self.csv_file.get_csv_columns():
                    value = context.resolve_attribute(column)
                    row[column] = value if value else ""
                
                self.csv_file.write_row(row)
                if self.csv_flush_every_message:
                    self.csv_file.flush()
                self.log_message(context, "debug", f"✅ CSV row written for message {context.message.name if context.message else 'unknown'}")
                return True
                
            except Exception as e:
                self.log_message(context, "error", f"❌ Error auto-writing to CSV for message {context.message.name if context.message else 'unknown'} - {context.session_id}: {e}")
                return False

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

    def register_owner(self, owner_app: Any):
        """Register an application instance as owner of this SessionManager.
        Key format: "ClassName(origin_host|fallback)". Idempotent per object.
        """
        if not owner_app:
            return None
        # Build origin host fallback safely
        origin_host = None
        try:
            if hasattr(owner_app, 'node') and hasattr(owner_app.node, 'origin_host'):
                origin_host = owner_app.node.origin_host
        except Exception:
            origin_host = None
        if not origin_host:
            fallback = getattr(owner_app, 'application_id', None)
            origin_host = fallback if fallback is not None else hex(id(owner_app))
        owner_key = f"{owner_app.__class__.__name__}({origin_host})"
        with self._owners_lock_context():
            # Remove stale keys pointing to same object
            stale_keys = [k for k, v in self.owners.items() if v is owner_app and k != owner_key]
            for k in stale_keys:
                del self.owners[k]
            self.owners[owner_key] = owner_app
        return owner_key

    def get_owners_by_app_id(self, app_id: int) -> List[Any]:
        """Return all registered owners with matching application_id."""
        with self._owners_lock_context():
            return [app for app in self.owners.values() if hasattr(app, 'application_id') and app.application_id == app_id]



