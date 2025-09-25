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
    session = app.get_session_by_id(message.session_id)
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
    session = app.get_session_by_id(message.session_id)
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
        # logger.info(f"🔄 CCR-I received, initiating spending limit check via Sy interface")
        
        # # 3GPP Flow: PCRF must check spending limits with OCS before authorizing session
        # spending_limit_result = _check_spending_limits_via_sy(app, message)
        
        # if spending_limit_result == E_RESULT_CODE_DIAMETER_SUCCESS:
        #     logger.info(f"✅ Spending limits OK, approving session {message.session_id}")
        #     answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
        # else:
        #     logger.warning(f"❌ Spending limits exceeded, rejecting session {message.session_id}")
        #     answer.result_code = spending_limit_result
        answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
            
    elif message.cc_request_type == E_CC_REQUEST_TYPE_UPDATE_REQUEST:
        # Session lookup handled by SessionManager
        gx_session = app.get_session_by_id(message.session_id)
        if not gx_session:
            raise ValueError(f"Session {message.session_id} not found")
        answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
    elif message.cc_request_type == E_CC_REQUEST_TYPE_TERMINATION_REQUEST:
        # Session lookup and termination handled by SessionManager
        gx_session = app.get_session_by_id(message.session_id)
        if not gx_session:
            raise ValueError(f"Session {message.session_id} not found")
        answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
        gx_session.end()
    return answer


def _check_spending_limits_via_sy(app: GxApplication, ccr_message: CreditControlRequest) -> int:
    """
    Implements the 3GPP Sy interface flow:
    PCRF sends SLR (Spending Limit Request) to OCS and waits for SLA (Spending Limit Answer)
    
    Returns:
        Result code from OCS (2001 = success, others = various error conditions)
    """
    from diameter.message.commands import SpendingLimitRequest
    from ..message import DiameterMessage
    from ..constants import APP_3GPP_SY
    
    try:
        logger.debug(f"🔍 Creating SLR for subscriber from CCR session {ccr_message.session_id}")
        
        # Create Spending Limit Request (SLR) based on CCR data
        slr = SpendingLimitRequest()
        slr.session_id = ccr_message.session_id  # Use same session ID for correlation
        slr.origin_host = ccr_message.destination_host  # PCRF is origin for SLR
        slr.origin_realm = ccr_message.destination_realm
        slr.destination_realm = ccr_message.destination_realm  # Same realm for OCS
        slr.auth_application_id = APP_3GPP_SY
        
        # Copy subscriber identification from CCR to SLR
        if hasattr(ccr_message, 'subscription_id'):
            slr.subscription_id = ccr_message.subscription_id
        
        # Wrap in DiameterMessage for our internal handling
        slr_dm = DiameterMessage(slr, APP_3GPP_SY)
        
        logger.info(f"📡 PCRF sending SLR to OCS for session {ccr_message.session_id}")
        
        # Get the Sy application from the same node that hosts this Gx application
        # The PCRF entity should have both gx_app and sy_app configured
        sy_app = None
        for node_app in app.node.applications.values():
            if hasattr(node_app, 'app_id') and node_app.app_id == APP_3GPP_SY:
                sy_app = node_app
                break
        
        if sy_app:
            logger.debug(f"🔗 Found Sy application on PCRF node, sending SLR")
            sla_dm = sy_app.send_request_custom(slr_dm, timeout=5)
            
            if sla_dm and hasattr(sla_dm.message, 'result_code'):
                result_code = sla_dm.message.result_code
                logger.info(f"📨 PCRF received SLA from OCS - Result: {result_code}")
                return result_code
            else:
                logger.error(f"❌ Invalid or missing SLA response from OCS")
                return E_RESULT_CODE_DIAMETER_UNABLE_TO_DELIVER
                
        else:
            logger.warning(f"⚠️  No Sy interface configured on PCRF, bypassing spending limit check")
            return E_RESULT_CODE_DIAMETER_SUCCESS  # Allow session if no OCS integration
            
    except Exception as e:
        logger.error(f"❌ Spending limit check failed: {e}")
        return E_RESULT_CODE_DIAMETER_UNABLE_TO_DELIVER