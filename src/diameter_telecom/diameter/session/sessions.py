from typing import Dict, Optional, List
from dataclasses import dataclass, field
import logging
from ._diameter_session import DiameterSession
from .gx import GxSession
from ..constants import APP_3GPP_GX, APP_3GPP_RX, APP_3GPP_SY

logger = logging.getLogger(__name__)

@dataclass
class Sessions:
    """Dedicated class for managing session collections and operations.
    
    This class handles all session data management including:
    - Session storage and retrieval
    - Indexing for fast lookups
    - Bulk operations and statistics
    - Session lifecycle management
    """
    sessions: Dict[int, Dict[str, DiameterSession]] = field(default_factory=dict)
    sessions_by_framed_ip: Dict[int, Dict[str, str]] = field(default_factory=dict)
    sessions_by_framed_ipv6: Dict[int, Dict[str, str]] = field(default_factory=dict)
    sessions_by_msisdn: Dict[int, Dict[str, str]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize all app_id dictionaries for supported applications."""
        # Initialize all app_id dictionaries
        for app_id in [APP_3GPP_GX, APP_3GPP_RX, APP_3GPP_SY]:
            self.sessions.setdefault(app_id, dict())
            self.sessions_by_framed_ip.setdefault(app_id, dict())
            self.sessions_by_framed_ipv6.setdefault(app_id, dict())
            self.sessions_by_msisdn.setdefault(app_id, dict())
    
    # Session CRUD operations
    def add_session(self, app_id: int, session: DiameterSession):
        """Add session and update all indexes.
        
        Args:
            app_id: Application ID (APP_3GPP_GX, APP_3GPP_RX, APP_3GPP_SY)
            session: Session instance to add
        """
        self.sessions[app_id][session.session_id] = session
        
        # Update indexes for Gx sessions (only Gx has these attributes)
        if app_id == APP_3GPP_GX and isinstance(session, GxSession):
            if session.framed_ip_address:
                self.sessions_by_framed_ip[app_id][session.framed_ip_address] = session.session_id
            if session.framed_ipv6_prefix:
                self.sessions_by_framed_ipv6[app_id][session.framed_ipv6_prefix] = session.session_id
            if session.subscriber and session.subscriber.msisdn:
                self.sessions_by_msisdn[app_id][session.subscriber.msisdn] = session.session_id
        
        logger.debug(f"Added session {session.session_id} for app_id {app_id}")
    
    def remove_session(self, app_id: int, session_id: str) -> Optional[DiameterSession]:
        """Remove session and clean up indexes.
        
        Args:
            app_id: Application ID
            session_id: Session ID to remove
            
        Returns:
            The removed session if found, None otherwise
        """
        session = self.sessions[app_id].pop(session_id, None)
        if not session:
            return None
            
        # Clean up indexes for Gx sessions
        if app_id == APP_3GPP_GX and isinstance(session, GxSession):
            if session.framed_ip_address:
                self.sessions_by_framed_ip[app_id].pop(session.framed_ip_address, None)
            if session.framed_ipv6_prefix:
                self.sessions_by_framed_ipv6[app_id].pop(session.framed_ipv6_prefix, None)
            if session.subscriber and session.subscriber.msisdn:
                self.sessions_by_msisdn[app_id].pop(session.subscriber.msisdn, None)
        
        logger.debug(f"Removed session {session_id} for app_id {app_id}")
        return session
    
    # Lookup methods
    def get_session_by_id(self, app_id: int, session_id: str) -> Optional[DiameterSession]:
        """Get session by application ID and session ID.
        
        Args:
            app_id: Application ID
            session_id: Session ID
            
        Returns:
            Session instance if found, None otherwise
        """
        return self.sessions.get(app_id, {}).get(session_id)
    
    def get_session_by_framed_ip(self, app_id: int, ip_address: str) -> Optional[DiameterSession]:
        """Get session by framed IP address.
        
        Args:
            app_id: Application ID
            ip_address: IP address to search for
            
        Returns:
            Session instance if found, None otherwise
        """
        session_id = self.sessions_by_framed_ip.get(app_id, {}).get(ip_address)
        if session_id:
            return self.get_session_by_id(app_id, session_id)
        return None
    
    def get_session_by_framed_ipv6(self, app_id: int, ipv6_prefix: str) -> Optional[DiameterSession]:
        """Get session by framed IPv6 prefix.
        
        Args:
            app_id: Application ID
            ipv6_prefix: IPv6 prefix to search for
            
        Returns:
            Session instance if found, None otherwise
        """
        session_id = self.sessions_by_framed_ipv6.get(app_id, {}).get(ipv6_prefix)
        if session_id:
            return self.get_session_by_id(app_id, session_id)
        return None
    
    def get_session_by_msisdn(self, app_id: int, msisdn: str) -> Optional[DiameterSession]:
        """Get session by MSISDN.
        
        Args:
            app_id: Application ID
            msisdn: MSISDN to search for
            
        Returns:
            Session instance if found, None otherwise
        """
        session_id = self.sessions_by_msisdn.get(app_id, {}).get(msisdn)
        if session_id:
            return self.get_session_by_id(app_id, session_id)
        return None
    
    # Bulk operations
    def get_all_sessions(self, app_id: int) -> Dict[str, DiameterSession]:
        """Get all sessions for an application.
        
        Args:
            app_id: Application ID
            
        Returns:
            Dictionary of session_id -> session for the application
        """
        return self.sessions.get(app_id, {})
    
    def get(self, app_id: int, default=None) -> Dict[str, DiameterSession]:
        """Get sessions for an application (backward compatibility method).
        
        This method provides backward compatibility with the old API where
        session_manager.sessions.get(APP_3GPP_GX, {}) was used.
        
        Args:
            app_id: Application ID
            default: Default value to return if app_id not found
            
        Returns:
            Dictionary of session_id -> session for the application
        """
        return self.sessions.get(app_id, default or {})
    
    def get_active_sessions(self, app_id: int) -> Dict[str, DiameterSession]:
        """Get only active sessions for an application.
        
        Args:
            app_id: Application ID
            
        Returns:
            Dictionary of active session_id -> session for the application
        """
        return {sid: session for sid, session in self.sessions.get(app_id, {}).items() 
                if session.active}
    
    def get_ended_sessions(self, app_id: int) -> Dict[str, DiameterSession]:
        """Get only ended sessions for an application.
        
        Args:
            app_id: Application ID
            
        Returns:
            Dictionary of ended session_id -> session for the application
        """
        return {sid: session for sid, session in self.sessions.get(app_id, {}).items() 
                if session.ended}
    
    def get_error_sessions(self, app_id: int) -> Dict[str, DiameterSession]:
        """Get only error sessions for an application.
        
        Args:
            app_id: Application ID
            
        Returns:
            Dictionary of error session_id -> session for the application
        """
        return {sid: session for sid, session in self.sessions.get(app_id, {}).items() 
                if session.error}
    
    def cleanup_inactive_sessions(self, app_id: int) -> int:
        """Remove inactive sessions (ended or error sessions).
        
        Args:
            app_id: Application ID
            
        Returns:
            Number of sessions removed
        """
        sessions_to_remove = []
        for session_id, session in self.sessions.get(app_id, {}).items():
            if session.ended or session.error:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            self.remove_session(app_id, session_id)
        
        logger.info(f"Cleaned up {len(sessions_to_remove)} inactive sessions for app_id {app_id}")
        return len(sessions_to_remove)
    
    def get_session_statistics(self, app_id: int) -> Dict[str, int]:
        """Get session statistics for an application.
        
        Args:
            app_id: Application ID
            
        Returns:
            Dictionary with session statistics
        """
        sessions = self.sessions.get(app_id, {})
        return {
            'total': len(sessions),
            'active': len([s for s in sessions.values() if s.active]),
            'ended': len([s for s in sessions.values() if s.ended]),
            'error': len([s for s in sessions.values() if s.error]),
            'inactive': len([s for s in sessions.values() if not s.active])
        }
    
    def get_all_statistics(self) -> Dict[int, Dict[str, int]]:
        """Get session statistics for all applications.
        
        Returns:
            Dictionary with app_id -> statistics mapping
        """
        return {
            app_id: self.get_session_statistics(app_id)
            for app_id in [APP_3GPP_GX, APP_3GPP_RX, APP_3GPP_SY]
        }
    
    def get_sessions_by_subscriber(self, app_id: int, msisdn: str) -> List[DiameterSession]:
        """Get all sessions for a specific subscriber.
        
        Args:
            app_id: Application ID
            msisdn: Subscriber MSISDN
            
        Returns:
            List of sessions for the subscriber
        """
        sessions = []
        for session in self.sessions.get(app_id, {}).values():
            if session.subscriber and session.subscriber.msisdn == msisdn:
                sessions.append(session)
        return sessions
    
    def update_session_indexes(self, app_id: int, session: DiameterSession):
        """Update indexes for an existing session (useful when session attributes change).
        
        Args:
            app_id: Application ID
            session: Session to update indexes for
        """
        if app_id == APP_3GPP_GX and isinstance(session, GxSession):
            # Remove old indexes first
            old_session = self.get_session_by_id(app_id, session.session_id)
            if old_session and isinstance(old_session, GxSession):
                if old_session.framed_ip_address:
                    self.sessions_by_framed_ip[app_id].pop(old_session.framed_ip_address, None)
                if old_session.framed_ipv6_prefix:
                    self.sessions_by_framed_ipv6[app_id].pop(old_session.framed_ipv6_prefix, None)
                if old_session.subscriber and old_session.subscriber.msisdn:
                    self.sessions_by_msisdn[app_id].pop(old_session.subscriber.msisdn, None)
            
            # Add new indexes
            if session.framed_ip_address:
                self.sessions_by_framed_ip[app_id][session.framed_ip_address] = session.session_id
            if session.framed_ipv6_prefix:
                self.sessions_by_framed_ipv6[app_id][session.framed_ipv6_prefix] = session.session_id
            if session.subscriber and session.subscriber.msisdn:
                self.sessions_by_msisdn[app_id][session.subscriber.msisdn] = session.session_id
    
    def clear_all_sessions(self, app_id: int):
        """Clear all sessions for an application.
        
        Args:
            app_id: Application ID
        """
        self.sessions[app_id].clear()
        self.sessions_by_framed_ip[app_id].clear()
        self.sessions_by_framed_ipv6[app_id].clear()
        self.sessions_by_msisdn[app_id].clear()
        logger.info(f"Cleared all sessions for app_id {app_id}")
    
    def clear_all_applications(self):
        """Clear all sessions for all applications."""
        for app_id in [APP_3GPP_GX, APP_3GPP_RX, APP_3GPP_SY]:
            self.clear_all_sessions(app_id)
        logger.info("Cleared all sessions for all applications")


    def to_json(self) -> dict:
        all_sessions = {}
        if self.sessions.get(APP_3GPP_GX):
            # It should be a list of sessions ordered by start_time
            all_sessions['gx_sessions'] = sorted(self.sessions.get(APP_3GPP_GX, {}).values(), key=lambda x: x.start_time)
            all_sessions['gx_sessions'] = [session.to_json() for session in all_sessions['gx_sessions']]
        if self.sessions.get(APP_3GPP_RX):
            all_sessions['rx_sessions'] = sorted(self.sessions.get(APP_3GPP_RX, {}).values(), key=lambda x: x.start_time)
            all_sessions['rx_sessions'] = [session.to_json() for session in all_sessions['rx_sessions']]
        if self.sessions.get(APP_3GPP_SY):
            all_sessions['sy_sessions'] = sorted(self.sessions.get(APP_3GPP_SY, {}).values(), key=lambda x: x.start_time)
            all_sessions['sy_sessions'] = [session.to_json() for session in all_sessions['sy_sessions']]
        return all_sessions