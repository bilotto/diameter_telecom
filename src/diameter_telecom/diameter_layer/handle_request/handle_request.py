import logging

from diameter.message.constants import *
from diameter.message.commands import *
from diameter.message.avp.grouped import *

from ... import Subscriber
from ...app.custom_simple_threading_application import CustomSimpleThreadingApplication
from ...message import DiameterMessage
from ...session.gx import GxSession
from ..parse_avp import *
from .gx import handle_request_gx
from .rx import handle_request_rx
from .sy import handle_request_sy

logger = logging.getLogger(__name__)

def handle_request(app: CustomSimpleThreadingApplication, message: Message):
    if app.application_id == APP_3GPP_GX:
        return handle_request_gx(app, message)
    elif app.application_id == APP_3GPP_RX:
        return handle_request_rx(app, message)
    elif app.application_id == APP_3GPP_SY:
        return handle_request_sy(app, message)


def handle_request_dsc(app: CustomSimpleThreadingApplication, message: Message):
    origin_host = message.origin_host
    origin_realm = message.origin_realm
    destination_host = message.destination_host
    destination_realm = message.destination_realm
    #
    message.route_record.append(origin_host)
    answer = app.send_request(message)
    return answer
