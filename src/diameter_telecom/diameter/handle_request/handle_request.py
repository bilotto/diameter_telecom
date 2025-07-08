from diameter.message.constants import *
from diameter.message.commands import *
from diameter.message.avp.grouped import *
from ..app import *
from ..message import DiameterMessage
from ..session import GxSession
from .. import Subscriber
from ..parse_avp import *
import logging
logger = logging.getLogger(__name__)

from .gx import handle_request_gx
from .rx import handle_request_rx
from .sy import handle_request_sy

def handle_request(app: CustomSimpleThreadingApplication, message: Message):
    if app.application_id == APP_3GPP_GX:
        return handle_request_gx(app, message)
    elif app.application_id == APP_3GPP_RX:
        return handle_request_rx(app, message)
    elif app.application_id == APP_3GPP_SY:
        return handle_request_sy(app, message)

