from diameter.message.constants import *
from diameter.message.commands import *
from diameter.message.avp.grouped import *
from ..app import RxApplication
from ..session import RxSession
from ..message import DiameterMessage
import logging
logger = logging.getLogger(__name__)

def handle_request_rx(app: RxApplication, message: Message):
    logger.info(f"Received message: {message}")
    answer = None
    rx_session = app.get_session_by_id(message.session_id)
    if not rx_session:
        answer = message.to_answer()
        answer.session_id = message.session_id
        answer.origin_host = message.destination_host
        answer.origin_realm = message.destination_realm
        answer.destination_host = message.origin_host
        answer.destination_realm = message.origin_realm
        answer.result_code = E_RESULT_CODE_DIAMETER_UNKNOWN_SESSION_ID
        return answer
    if isinstance(message, ReAuthRequest):
        answer = handle_rar(app, message)
    elif isinstance(message, AbortSessionRequest):
        answer = handle_asr(app, message)
    return answer

def handle_rar(app: RxApplication, message: ReAuthRequest):
    answer = message.to_answer()
    if not isinstance(answer, ReAuthAnswer):
        raise ValueError("Answer is not ReAuthAnswer")
    answer.session_id = message.session_id
    answer.origin_host = message.destination_host
    answer.origin_realm = message.destination_realm
    answer.destination_host = message.origin_host
    answer.destination_realm = message.origin_realm
    #
    session_id = message.session_id
    session = app.get_session_by_id(session_id)
    if not session:
        answer.result_code = E_RESULT_CODE_DIAMETER_UNKNOWN_SESSION_ID
    else:
        req_diameter_message = DiameterMessage(message)
        session.add_message(req_diameter_message)
        answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
        session.add_message(answer)
    return answer


def handle_asr(app: RxApplication, message: AbortSessionRequest):
    answer = message.to_answer()
    if not isinstance(answer, AbortSessionAnswer):
        raise ValueError("Answer is not AbortSessionAnswer")
    answer.session_id = message.session_id
    answer.origin_host = message.destination_host
    answer.origin_realm = message.destination_realm
    answer.destination_host = message.origin_host
    answer.destination_realm = message.origin_realm
    #
    session_id = message.session_id
    session = app.get_session_by_id(session_id)
    if not session:
        answer.result_code = E_RESULT_CODE_DIAMETER_UNKNOWN_SESSION_ID
        return answer
    req_diameter_message = DiameterMessage(message)
    session.add_message(req_diameter_message)
    answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
    session.add_message(answer)
    app.terminate_session_after_successful_abort(session_id)
    return answer
