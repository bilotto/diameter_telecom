import threading
from typing import Optional

from .session_manager import SessionManager


_lock: threading.RLock = threading.RLock()
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
	"""Return the shared SessionManager instance (lazy singleton)."""
	global _session_manager
	with _lock:
		if _session_manager is None:
			_session_manager = SessionManager()
		return _session_manager


def set_session_manager(session_manager: SessionManager) -> None:
	"""Set/replace the shared SessionManager instance.

	Use to inject a custom instance or reset state for tests.
	"""
	global _session_manager
	with _lock:
		_session_manager = session_manager


def new_context() -> SessionManager:
	"""Create a fresh, independent SessionManager (not registered as shared)."""
	return SessionManager()


