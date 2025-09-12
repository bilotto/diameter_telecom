from ..subscriber import Subscriber, Subscribers
from .session import GxSession, RxSession, SySession, DiameterSession
from .session.sessions import Sessions
from .message_processing_pipeline import MessageProcessingPipeline
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import threading
import time
import logging
from .constants import *
from .parse_avp import *
from .message import DiameterMessage

logger = logging.getLogger(__name__)

@dataclass
class SessionManager:
    """Centralized session and subscriber management for Diameter applications.
    
    This class handles high-level orchestration of message processing and maintains
    the data stores for sessions, subscribers, and messages. The actual message 
    processing logic is delegated to MessageProcessingPipeline.
    """
    sessions: Sessions = field(default_factory=Sessions)
    subscribers: Subscribers = field(default_factory=Subscribers)
    messages: List[DiameterMessage] = field(default_factory=list)
    pipeline: MessageProcessingPipeline = field(init=False)

    def __post_init__(self):
        """Initialize the message processing pipeline"""
        self.pipeline = MessageProcessingPipeline(
            sessions=self.sessions,
            subscribers=self.subscribers
        )

    def get_messages(self):
        return sorted(self.messages, key=lambda x: x.timestamp if x.timestamp else float('inf'))

    def process_diameter_message(self, dm: DiameterMessage):
        """Main entry point for processing Diameter messages.
        
        This method orchestrates the message processing by delegating to the
        MessageProcessingPipeline and handling the final message storage.
        """
        # Setup processing context
        gv_stages = dict()
        if not dm.timestamp:
            dm.timestamp = time.time()
        gv_stages['dm'] = dm
        gv_stages['session_id'] = dm.session_id
        gv_stages['app_id'] = dm.app_id
        logger.info(f"Processing {dm.name} - {dm.session_id}")
        
        # Delegate to pipeline for processing
        if dm.is_request:
            self.pipeline.stage_parse_request(gv_stages)
        else:
            self.pipeline.stage_parse_response(gv_stages)
        
        # Process application-specific business logic
        self.pipeline.process_app_specific_logic(gv_stages)
        
        # Handle final message storage and association
        session = gv_stages.get('session')
        if session:
            session.messages.append(dm)
            subscriber = gv_stages.get('subscriber')
            if subscriber:
                subscriber.add_message(dm)
                dm.subscriber = subscriber

        self.messages.append(dm)

    def send_request_with_session_management(self, diameter_message: DiameterMessage, send_request_func, timeout=10) -> DiameterMessage:
        self.process_diameter_message(diameter_message)
        logger.info(f"\n{diameter_message.dump()}")
        
        answer = send_request_func(diameter_message.message, timeout=timeout)
        diameter_message_answer = DiameterMessage(answer)
        
        self.process_diameter_message(diameter_message_answer)
        
        if diameter_message_answer.result_code != E_RESULT_CODE_DIAMETER_SUCCESS:
            logger.error(f"Answer with error: \n {diameter_message_answer}")
        logger.info(f"\n{diameter_message_answer.dump()}")
        
        return diameter_message_answer

    def to_json(self) -> dict:
        """
        Convert SessionManager to JSON-serializable dictionary.
        
        Returns:
            dict: JSON-serializable representation of the session manager
        """
        try:
            # Extract sessions data
            sessions_data = {}
            if hasattr(self.sessions, 'sessions'):
                for app_id, app_sessions in self.sessions.sessions.items():
                    app_name = self._get_app_name(app_id)
                    sessions_data[app_name] = {
                        "app_id": app_id,
                        "total_sessions": len(app_sessions),
                        "sessions": {}
                    }
                    
                    for session_id, session in app_sessions.items():
                        if hasattr(session, 'to_json'):
                            sessions_data[app_name]["sessions"][session_id] = session.to_json()
                        else:
                            # Fallback for sessions without to_json method
                            sessions_data[app_name]["sessions"][session_id] = {
                                "session_id": session_id,
                                "error": "Session serialization not available"
                            }
            
            # Extract subscribers data
            subscribers_data = {}
            if hasattr(self.subscribers, 'subscribers'):
                for msisdn, subscriber in self.subscribers.subscribers.items():
                    if hasattr(subscriber, 'to_json'):
                        subscribers_data[msisdn] = subscriber.to_json()
                    else:
                        # Fallback for subscribers without to_json method
                        subscribers_data[msisdn] = {
                            "msisdn": msisdn,
                            "error": "Subscriber serialization not available"
                        }
            
            # Extract messages data
            messages_data = []
            for message in self.messages[:100]:  # Limit to first 100 messages for performance
                if hasattr(message, 'to_json'):
                    messages_data.append(message.to_json())
                else:
                    # Fallback for messages without to_json method
                    messages_data.append({
                        "session_id": getattr(message, "session_id", None),
                        "name": getattr(message, "name", None),
                        "error": "Message serialization not available"
                    })
            
            # Calculate comprehensive statistics
            stats = self._calculate_statistics(sessions_data, subscribers_data, messages_data)
            
            return {
                "statistics": stats,
                "sessions": sessions_data,
                "subscribers": subscribers_data,
                "messages": {
                    "total_count": len(self.messages),
                    "sample_messages": messages_data
                }
            }
            
        except Exception as e:
            logger.exception("SessionManager JSON serialization failed")
            return {"error": f"Failed to serialize session manager: {str(e)}"}

    def _get_app_name(self, app_id: int) -> str:
        """Convert application ID to readable name."""
        app_names = {
            16777238: "Gx",  # APP_3GPP_GX
            16777236: "Rx",  # APP_3GPP_RX  
            16777302: "Sy"   # APP_3GPP_SY
        }
        return app_names.get(app_id, f"App_{app_id}")

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
