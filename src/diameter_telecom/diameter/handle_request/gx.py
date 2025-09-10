from diameter.message.constants import *
from diameter.message.commands import *
from diameter.message.avp.grouped import *
from ..app import GxApplication
from ..message import DiameterMessage
from ..session import GxSession
from .. import Subscriber
from ..parse_avp import *
import logging
logger = logging.getLogger(__name__)

def handle_request_gx(app: GxApplication, message: Message):
    answer = None
    if isinstance(message, ReAuthRequest):
        answer = handle_rar(app, message)
    elif isinstance(message, AbortSessionRequest):
        answer = handle_asr(app, message)
    elif isinstance(message, CreditControlRequest):
        answer = handle_ccr(app, message)
    return answer

def handle_rar(app: GxApplication, message: ReAuthRequest):
    answer = message.to_answer()
    if not isinstance(answer, ReAuthAnswer):
        raise ValueError("Answer is not ReAuthAnswer")
    answer.session_id = message.session_id
    answer.origin_host = message.destination_host
    answer.origin_realm = message.destination_realm
    # answer.destination_host = message.origin_host
    # answer.destination_realm = message.origin_realm
    #
    # Session management handled by SessionManager
    session = app.get_gx_session_by_id(message.session_id)
    if not session:
        answer.result_code = E_RESULT_CODE_DIAMETER_UNKNOWN_SESSION_ID
    else:
        # Message processing handled by SessionManager
        answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
    return answer

def handle_asr(app: GxApplication, message: AbortSessionRequest):
    answer = message.to_answer()
    if not isinstance(answer, AbortSessionAnswer):
        raise ValueError("Answer is not AbortSessionAnswer")
    answer.session_id = message.session_id
    answer.origin_host = message.destination_host
    answer.origin_realm = message.destination_realm
    #
    # Session management handled by SessionManager
    session = app.get_gx_session_by_id(message.session_id)
    if not session:
        answer.result_code = E_RESULT_CODE_DIAMETER_UNKNOWN_SESSION_ID
    else:
        # Message processing handled by SessionManager
        answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
    return answer


def handle_ccr(app: GxApplication, message: CreditControlRequest):
    answer = message.to_answer()
    answer.cc_request_number = message.cc_request_number
    answer.cc_request_type = message.cc_request_type
    if not isinstance(answer, CreditControlAnswer):
        raise ValueError("Answer is not CreditControlAnswer")
    answer.session_id = message.session_id
    answer.origin_host = message.destination_host
    answer.origin_realm = message.destination_realm
    answer.auth_application_id = message.auth_application_id
    answer.cc_request_type = message.cc_request_type
    answer.cc_request_number = message.cc_request_number

    # Session and subscriber management is now handled by SessionManager
    # Just focus on business logic here
    if message.cc_request_type == E_CC_REQUEST_TYPE_INITIAL_REQUEST:
        # Session creation and subscriber identification handled by SessionManager
        answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
    elif message.cc_request_type == E_CC_REQUEST_TYPE_UPDATE_REQUEST:
        # Session lookup handled by SessionManager
        gx_session = app.get_gx_session_by_id(message.session_id)
        if not gx_session:
            raise ValueError(f"Session {message.session_id} not found")
        answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
    elif message.cc_request_type == E_CC_REQUEST_TYPE_TERMINATION_REQUEST:
        # Session lookup and termination handled by SessionManager
        gx_session = app.get_gx_session_by_id(message.session_id)
        if not gx_session:
            raise ValueError(f"Session {message.session_id} not found")
        answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
        gx_session.end()
    return answer