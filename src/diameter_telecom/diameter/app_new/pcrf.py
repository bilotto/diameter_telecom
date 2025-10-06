from .common import CommonThreadingApplication
from diameter.message.constants import *
from diameter.message import Message
from diameter.message.commands import CreditControlRequest, CreditControlAnswer
from diameter.message.avp import *
from diameter.message.avp.grouped import *
# from diameter_telecom import GxSession, Subscriber
# from diameter_telecom.diameter.message import DiameterMessage, create_message
# from diameter_telecom.apn import ip_to_bytes
# from diameter_telecom.diameter.constants import *
# from diameter_telecom.diameter.parse_avp import *
from typing import List
from ..message import DiameterMessage, create_message
from ..session.gx import GxSession
from ..session.rx import RxSession
from ..session.sy import SySession
from ..constants import *
from ..parse_avp import *

class PcrfGxApplication(CommonThreadingApplication):
    def __init__(self, max_threads: int = 1):
        super().__init__(application_id=APP_3GPP_GX, is_acct_application=False, is_auth_application=True, max_threads=max_threads)
        self.related_apps: List[CommonThreadingApplication] = []

    @property
    def rx_app(self) -> CommonThreadingApplication:
        return self.get_related_app(APP_3GPP_RX)

    @property
    def sy_app(self) -> CommonThreadingApplication:
        return self.get_related_app(APP_3GPP_SY)

    def get_related_app(self, app_id: int) -> CommonThreadingApplication:
        for app in self.related_apps:
            if app.application_id == app_id:
                return app
        return None

    def get_session_by_id(self, session_id: str) -> GxSession:
        return self.session_manager.sessions.get_session_by_id(APP_3GPP_GX, session_id)

    def handle_request(self, message: CreditControlRequest) -> CreditControlAnswer:
        answer = message.to_answer()
        answer.cc_request_number = message.cc_request_number
        answer.cc_request_type = message.cc_request_type
        if not isinstance(answer, CreditControlAnswer):
            self.logger.error(f"❌ Gx CCR: Invalid answer type {type(answer)} for session {message.session_id}")
            raise ValueError("Answer is not CreditControlAnswer")
            
        answer.session_id = message.session_id
        answer.origin_host = message.destination_host
        answer.origin_realm = message.destination_realm
        answer.destination_realm = message.destination_realm
        answer.destination_host = message.destination_host
        answer.auth_application_id = message.auth_application_id
        answer.cc_request_type = message.cc_request_type
        answer.cc_request_number = message.cc_request_number

        subscriber = None

        if message.subscription_id:
            msisdn, imsi, _, _, _ = parse_subscription_id(message.subscription_id)
            self.logger.debug(f"🔍 Gx CCR: Parsed subscription - MSISDN: {msisdn}, IMSI: {imsi}")
            if msisdn:
                subscriber = self.subscribers.get_subscriber_by_msisdn(msisdn)
                self.logger.debug(f"👤 Gx CCR: Found subscriber by MSISDN: {subscriber}")
            elif imsi:
                subscriber = self.subscribers.get_subscriber_by_imsi(imsi)
                self.logger.debug(f"👤 Gx CCR: Found subscriber by IMSI: {imsi}")
        else:
            self.logger.debug(f"⚠️ Gx CCR: No subscription ID in message for session {message.session_id}")

        # Session and subscriber management is now handled by SessionManager
        # Just focus on business logic here
        if message.cc_request_type == E_CC_REQUEST_TYPE_INITIAL_REQUEST:
            self.logger.info(f"🆕 Gx CCR: Processing INITIAL request for session {message.session_id}")
            # answer.event_trigger.append(E_EVENT_TRIGGER_RAT_CHANGE)
            # answer.event_trigger.append(E_EVENT_TRIGGER_QOS_CHANGE)
            answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
            answer.charging_rule_install.append(ChargingRuleInstall("FREE_SERVICES"))
            if subscriber:
                answer.charging_rule_install.append(ChargingRuleInstall("SUBSCRIBER_INTERNET"))
                self.logger.debug(f"✅ Gx CCR: Added INTERNET rule for subscriber")
            else:
                answer.charging_rule_install.append(ChargingRuleInstall("SUBSCRIBER_BLOCK"))
                self.logger.debug(f"🚫 Gx CCR: Added BLOCK rule for unknown subscriber")
            answer.charging_rule_install.append(ChargingRuleInstall("WEB_PORTAL"))
            self.logger.info(f"✅ Gx CCR: INITIAL request processed successfully for session {message.session_id}")

            if message.rat_type and message.rat_type == E_RAT_TYPE_EUTRAN:
                answer.charging_rule_install.append(ChargingRuleInstall("EUTRAN_SERVICE"))
                answer.event_trigger.append(E_EVENT_TRIGGER_RAT_CHANGE)
            elif message.rat_type and message.rat_type == E_RAT_TYPE_GERAN:
                answer.charging_rule_install.append(ChargingRuleInstall("GERAN_SERVICE"))
                answer.event_trigger.append(E_EVENT_TRIGGER_RAT_CHANGE)
            elif message.rat_type and message.rat_type == E_RAT_TYPE_UTRAN:
                answer.charging_rule_install.append(ChargingRuleInstall("UTRAN_SERVICE"))
                answer.event_trigger.append(E_EVENT_TRIGGER_RAT_CHANGE)

            if subscriber and self.sy_app:
                # ocs data flow
                pass
            if not subscriber and self.rx_app:
                # voice flow
                pass
                
        elif message.cc_request_type == E_CC_REQUEST_TYPE_UPDATE_REQUEST:
            self.logger.info(f"🔄 Gx CCR: Processing UPDATE request for session {message.session_id}")
            # Session lookup handled by SessionManager
            gx_session = self.get_session_by_id(message.session_id)
            if not gx_session:
                self.logger.error(f"❌ Gx CCR: Session {message.session_id} not found for UPDATE request")
                raise ValueError(f"Session {message.session_id} not found")
            answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
            self.logger.info(f"✅ Gx CCR: UPDATE request processed successfully for session {message.session_id}")
            
        elif message.cc_request_type == E_CC_REQUEST_TYPE_TERMINATION_REQUEST:
            self.logger.info(f"🛑 Gx CCR: Processing TERMINATION request for session {message.session_id}")
            # Session lookup and termination handled by SessionManager
            gx_session = self.get_session_by_id(message.session_id)
            if not gx_session:
                self.logger.error(f"❌ Gx CCR: Session {message.session_id} not found for TERMINATION request")
                raise ValueError(f"Session {message.session_id} not found")
            answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
            gx_session.end()
            self.logger.info(f"✅ Gx CCR: TERMINATION request processed successfully for session {message.session_id}")
        else:
            self.logger.warning(f"⚠️ Gx CCR: Unknown CC request type {message.cc_request_type} for session {message.session_id}")
            
        self.logger.debug(f"💳 Gx CCR: Returning CreditControlAnswer with result code {answer.result_code} for session {message.session_id}")
        return answer


class PcrfRxApplication(CommonThreadingApplication):
    def __init__(self, max_threads: int = 1):
        super().__init__(application_id=APP_3GPP_RX, is_acct_application=False, is_auth_application=True, max_threads=max_threads)

    def create_session(self) -> RxSession:
        pass
        raise NotImplementedError("PCRF does not create Rx sessions. Use AF to create Rx sessions along with PCEF.")

    def handle_request(self, message: Message):
        answer = message.to_answer()
        answer.cc_request_number = message.cc_request_number
        answer.cc_request_type = message.cc_request_type
        return answer
    
    def create_message(self, message_name: str) -> CreditControlRequest:
        if message_name not in [CCR_I, CCR_U, CCR_T]:
            raise ValueError(f"Invalid message name: {message_name}")
        request = CreditControlRequest()
        request.header.application_id = APP_3GPP_RX
        request.auth_application_id = APP_3GPP_RX
        request.session_id = self.node.session_generator.next_id()
        request.origin_host = self.node.origin_host.encode()
        request.origin_realm = self.node.realm_name.encode()
        request.destination_realm = self.node.realm_name.encode()



class PcrfSyApplication(CommonThreadingApplication):
    def __init__(self, max_threads: int = 1):
        super().__init__(application_id=APP_3GPP_SY, is_acct_application=False, is_auth_application=True, max_threads=max_threads)
        self.related_apps: List[CommonThreadingApplication] = []

    def create_session(self) -> SySession:
        # PCRF does create Sy sessions
        pass

    def handle_request(self, message: Message):
        answer = message.to_answer()
        answer.cc_request_number = message.cc_request_number
        answer.cc_request_type = message.cc_request_type
        return answer