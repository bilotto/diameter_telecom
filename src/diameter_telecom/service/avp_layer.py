from typing import List, Dict, Any
import logging
logger = logging.getLogger(__name__)

from ..session._diameter_session import DiameterSession
from ..message import DiameterMessage, Message
from ..app_new.common import CommonThreadingApplication
from ..subscriber import Subscriber

def apply_avp_layers(request: Message,
                    app: CommonThreadingApplication = None,
                    session: DiameterSession = None,
                    subscriber: Subscriber = None,
                    custom_avps: List[Dict[str, Any]] = None) -> Message:
    """
    Apply AVP layers to a Diameter request message.
    
    Args:
        request: Message to apply AVPs to
        app: Application to apply AVPs to
        session: Diameter session to apply AVPs to
        subscriber: Subscriber to apply AVPs to
        custom_avps: Optional list of custom AVPs to apply
        
    Returns:
        Message with AVPs applied
    """

    if app:
        request = app.add_avps(request)
    if session:
        request = session.add_avps(request)
    if subscriber:
        request = subscriber.add_avps(request)
    if custom_avps:
        for avp in custom_avps:
            avp_name = avp.get("name")
            avp_value = avp.get("value")
            if hasattr(request, avp_name):
                setattr(request, avp_name, avp_value)
                logger.debug(f"Custom AVP: {avp_name} = {avp_value}")
                
    return request
