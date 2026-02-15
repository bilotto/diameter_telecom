from typing import Optional
from .base import ProcessingStage
from .constants import *
from ..message_processing_context import MessageProcessingContext
from ...subscriber import Subscriber
from ...constants import APP_3GPP_GX


class SubscriberResolutionStage(ProcessingStage):
    """Finds or creates subscriber based on message data."""
    
    def __init__(self):
        super().__init__(STAGE_SUBSCRIBER_RESOLUTION)
    
    def execute(self, context: MessageProcessingContext) -> None:
        """Find or create subscriber based on message data."""
        self.log_stage(context, "debug", f"✅ Resolving subscriber")
        
        # Skip if subscriber already found
        if context.subscriber_found:
            self.log_stage(context, "debug", "📋 Subscriber already resolved - skipping")
            return
        
        # Get collections from context
        subscribers = getattr(context, 'subscribers', None)
        sessions = getattr(context, 'sessions', None)
        
        if not subscribers:
            self.log_stage(context, "error", "❌ Subscribers collection not available in context")
            context.subscriber = None
            context.subscriber_found = False
            context.subscriber_created = False
            return
        
        subscriber = None
        resolution_method = None
        
        try:
            # Method 0: Check if we already have a session with a subscriber (HIGHEST PRIORITY)
            if context.session and context.session.subscriber:
                subscriber = context.session.subscriber
                resolution_method = RESOLUTION_EXISTING_SESSION
                self.log_stage(context, "debug", f"✅ Subscriber found from existing session: {subscriber.msisdn}")
            
            # Method 1: Try to find subscriber by MSISDN
            if not subscriber and context.msisdn:
                self.log_stage(context, "debug", f"🔍 Resolving subscriber by MSISDN: {context.msisdn}")
                subscriber = subscribers.get_subscriber_by_msisdn(context.msisdn)
                if subscriber:
                    resolution_method = RESOLUTION_MSISDN
                    self.log_stage(context, "debug", f"✅ Subscriber found by MSISDN: {context.msisdn}")
            
            # Method 2: Try to find subscriber by IMSI
            if not subscriber and context.imsi:
                self.log_stage(context, "debug", f"🔍 Resolving subscriber by IMSI: {context.imsi}")
                subscriber = subscribers.get_subscriber_by_imsi(context.imsi)
                if subscriber:
                    resolution_method = RESOLUTION_IMSI
                    self.log_stage(context, "debug", f"✅ Subscriber found by IMSI: {context.imsi}")
            
            # Method 3: Try to find subscriber by framed IP address (via Gx session)
            if not subscriber and context.framed_ip_address and sessions:
                self.log_stage(context, "debug", f"🔍 Resolving subscriber by framed IP address: {context.framed_ip_address}")
                gx_session = sessions.get_session_by_framed_ip(APP_3GPP_GX, context.framed_ip_address)
                if gx_session and gx_session.subscriber:
                    subscriber = gx_session.subscriber
                    resolution_method = RESOLUTION_FRAMED_IP
                    self.log_stage(context, "debug", f"✅ Subscriber found by framed IP address: {context.framed_ip_address}")
            
            # Method 4: Create new subscriber if none found (requests only; answers typically don't carry MSISDN/IMSI)
            if not subscriber:
                self.log_stage(context, "debug", f"🔍 No subscriber found. Creating new subscriber.")
                subscriber = self._create_subscriber(context, subscribers)
                if subscriber:
                    resolution_method = RESOLUTION_CREATED
                    self.log_stage(context, "debug", f"✅ New subscriber created: {subscriber.msisdn}")
            
            # Ensure subscriber is in the collection if found
            if subscriber and resolution_method != RESOLUTION_CREATED:
                # Subscriber was found, ensure it's in the collection
                self._ensure_subscriber_in_collection(subscriber, subscribers, resolution_method, context)
            
            # Set context results
            context.subscriber = subscriber
            context.subscriber_found = subscriber is not None
            context.subscriber_created = (resolution_method == RESOLUTION_CREATED)
            context.subscriber_resolution_method = resolution_method
            
            if subscriber:
                self.log_stage(context, "debug", f"📊 Subscriber resolved via {resolution_method}: MSISDN={subscriber.msisdn}, IMSI={getattr(subscriber, 'imsi', 'N/A')}")
            elif context.is_request:
                self.log_stage(context, "warning", f"⚠️ Failed to resolve or create subscriber")
            else:
                self.log_stage(context, "debug", f"Subscriber not resolved (answer message, no MSISDN/IMSI - expected)")
                
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error during subscriber resolution: {e}")
            context.subscriber = None
            context.subscriber_found = False
            context.subscriber_created = False
    
    def _ensure_subscriber_in_collection(self, subscriber: Subscriber, subscribers, resolution_method: str, context: MessageProcessingContext):
        """Ensure subscriber is in the subscribers collection."""
        try:
            # Check if subscriber is already in collection by MSISDN or IMSI
            existing_subscriber = None
            if subscriber.msisdn:
                existing_subscriber = subscribers.get_subscriber_by_msisdn(subscriber.msisdn)
            elif subscriber.imsi:
                existing_subscriber = subscribers.get_subscriber_by_imsi(subscriber.imsi)
            
            if existing_subscriber:
                # Subscriber already in collection - use the one from collection
                if existing_subscriber is not subscriber:
                    self.log_stage(context, "debug", f"📋 Subscriber already in collection, using existing instance: {subscriber.msisdn}")
                    # Update context to use the subscriber from collection
                    context.subscriber = existing_subscriber
                else:
                    self.log_stage(context, "debug", f"📋 Subscriber already in collection: {subscriber.msisdn}")
            else:
                # Subscriber not in collection - add it
                subscribers.add_subscriber(subscriber)
                self.log_stage(context, "debug", f"✅ Added found subscriber to collection: MSISDN={subscriber.msisdn}, method={resolution_method}")
                
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error ensuring subscriber in collection: {e}")
    
    def _create_subscriber(self, context: MessageProcessingContext, subscribers) -> Optional[Subscriber]:
        """Create a new subscriber based on context data."""
        try:
            # Extract MSISDN and IMSI from context
            msisdn = context.msisdn
            imsi = context.imsi
            
            # If we don't have MSISDN or IMSI, we can't create a subscriber.
            # Answers (e.g. CCA) typically don't carry MSISDN/IMSI - only log for requests.
            if not msisdn and not imsi:
                if context.is_request:
                    self.log_stage(context, "warning", f"⚠️ Cannot create subscriber: no MSISDN or IMSI available")
                return None
            
            # Create new subscriber
            subscriber = Subscriber(msisdn=msisdn, imsi=imsi)
            
            # Add to subscribers collection
            subscribers.add_subscriber(subscriber)
            
            self.log_stage(context, "debug", f"✅ Subscriber created and added to collection: MSISDN={msisdn}, IMSI={imsi}")
            return subscriber
            
        except Exception as e:
            self.log_stage(context, "error", f"❌ Error creating subscriber: {e}")
            return None
