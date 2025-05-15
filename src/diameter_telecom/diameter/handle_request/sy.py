from diameter.message.constants import *
from diameter.message.commands import *
from diameter.message.avp.grouped import *
from ..app import SyApplication
from ..session import SySession
from ..message import DiameterMessage
from ..parse_avp import *
import logging
logger = logging.getLogger(__name__)

def handle_request_sy(app: SyApplication, message: Message):
    answer = message.to_answer()
    msisdn, imsi, sip_uri, nai, private = parse_subscription_id(message.subscription_id)
    if not isinstance(answer, SpendingLimitAnswer):
        raise ValueError("Answer is not SpendingLimitAnswer")
    answer.session_id = message.session_id
    answer.origin_host = app.node.origin_host.encode()
    answer.origin_realm = app.node.realm_name.encode()
    answer.auth_application_id = message.auth_application_id
    #
    answer.policy_counter_status_report = []
    sla_policy_counter_dict = {
        "internet": "true",
    }
    for k, v in sla_policy_counter_dict.items():
        pcsr = PolicyCounterStatusReport()
        pcsr.policy_counter_identifier = k
        pcsr.policy_counter_status = v
        answer.policy_counter_status_report.append(pcsr)
    answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
    return answer
