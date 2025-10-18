from typing import List

from diameter.message import Message
from diameter.message.commands import (
    CreditControlRequest, 
    CreditControlAnswer, 
    SpendingLimitRequest, 
    SpendingStatusNotificationRequest, 
    SessionTerminationRequest
)
from diameter.message.constants import *

from ..constants import *
from ..diameter_layer.parse_avp import *
from ..message import DiameterMessage, create_message
from ..session.gx import GxSession
from ..session.rx import RxSession
from ..session.sy import SySession
from .common import CommonThreadingApplication

from ..diameter_layer import ChargingRuleInstall, QosInformation, DefaultEpsBearerQos, AllocationRetentionPriority

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

    def _handle_request(self, message: CreditControlRequest) -> CreditControlAnswer:
        answer: CreditControlAnswer = message.to_answer()
        answer.cc_request_number = message.cc_request_number
        answer.cc_request_type = message.cc_request_type
        answer.session_id = message.session_id
        answer.origin_host = message.destination_host
        answer.origin_realm = message.destination_realm
        answer.destination_realm = message.destination_realm
        answer.destination_host = message.destination_host
        answer.auth_application_id = message.auth_application_id
        answer.cc_request_type = message.cc_request_type
        answer.cc_request_number = message.cc_request_number

        subscriber = None
        gx_session = None
        if self.session_manager.sessions.get_session_by_id(APP_3GPP_GX, message.session_id):
            gx_session = self.session_manager.sessions.get_session_by_id(APP_3GPP_GX, message.session_id)
        else:
            self.logger.error(f"{__class__.__name__}❌ Gx CCR: Session {message.session_id} not found for request. Client and Server are not sharing the same session manager.")
            pass

        if gx_session:
            subscriber = gx_session.subscriber
        elif message.subscription_id:
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

            # Add QoS Information
            qos_info = QosInformation()
            qos_info.qos_class_identifier = E_QOS_CLASS_IDENTIFIER_QCI_8  # Default QCI 8 for internet
            qos_info.max_requested_bandwith_ul = 1000000  # 1 Mbps UL
            qos_info.max_requested_bandwith_dl = 10000000  # 10 Mbps DL
            qos_info.guaranteed_bitrate_ul = 500000  # 500 kbps UL
            qos_info.guaranteed_bitrate_dl = 5000000  # 5 Mbps DL
            answer.qos_information = qos_info
            self.logger.debug(f"✅ Gx CCR: Added QoS Information - QCI: {qos_info.qos_class_identifier}")

            # Add Default EPS Bearer QoS
            default_qos = DefaultEpsBearerQos()
            default_qos.qos_class_identifier = E_QOS_CLASS_IDENTIFIER_QCI_9  # QCI 9 for default bearer
            default_qos.allocation_retention_priority = AllocationRetentionPriority()
            default_qos.allocation_retention_priority.priority_level = 15  # Standard priority
            default_qos.allocation_retention_priority.pre_emption_vulnerability = 1  # Pre-emption vulnerable
            default_qos.allocation_retention_priority.pre_emption_capability = 0  # No pre-emption capability
            answer.default_eps_bearer_qos = default_qos
            self.logger.debug(f"✅ Gx CCR: Added Default EPS Bearer QoS - QCI: {default_qos.qos_class_identifier}")


            if message.rat_type and message.rat_type == E_RAT_TYPE_EUTRAN:
                answer.charging_rule_install.append(ChargingRuleInstall("EUTRAN_SERVICE"))
                answer.event_trigger.append(E_EVENT_TRIGGER_RAT_CHANGE)
            elif message.rat_type and message.rat_type == E_RAT_TYPE_GERAN:
                answer.charging_rule_install.append(ChargingRuleInstall("GERAN_SERVICE"))
                answer.event_trigger.append(E_EVENT_TRIGGER_RAT_CHANGE)
            elif message.rat_type and message.rat_type == E_RAT_TYPE_UTRAN:
                answer.charging_rule_install.append(ChargingRuleInstall("UTRAN_SERVICE"))
                answer.event_trigger.append(E_EVENT_TRIGGER_RAT_CHANGE)

            if self.sy_app:
                self.logger.debug(f"{__class__.__name__}✅ PCRF with Sy application")
                if subscriber:
                    try:
                        sy_session: SySession = self.sy_app.create_session(subscriber)
                        sy_session.gx_session_id = message.session_id
                        self.logger.debug(f"{__class__.__name__}✅ Gx CCR: Created Sy session for subscriber {subscriber.msisdn} with session ID {sy_session.session_id}")
                        request = self.sy_app.create_request(SLR, sy_session)
                        self.logger.debug(f"{__class__.__name__}✅ Gx CCR: Created request for subscriber {subscriber.msisdn} with session ID {sy_session.session_id}")
                        sy_diameter_answer = self.sy_app.send_request_custom(request, timeout=2)
                        # sy_answer = sy_diameter_answer.message
                        self.logger.debug(f"{__class__.__name__}✅ Gx CCR: Sent request for subscriber {subscriber.msisdn} with session ID {sy_session.session_id}")
                        answer.charging_rule_install.append(ChargingRuleInstall("PCRF_SY_CALLED"))
                        if answer.result_code != E_RESULT_CODE_DIAMETER_SUCCESS:
                            self.logger.error(f"{__class__.__name__}❌ Gx CCR: Failed to create session for subscriber {subscriber.msisdn} with result code {answer.result_code}")
                            pass
                        # ocs data flow
                        pass
                    except Exception as e:
                        answer.charging_rule_install.append(ChargingRuleInstall("PCRF_SY_ERROR"))
                        self.logger.error(f"{__class__.__name__}❌ Gx CCR: Failed to create session for subscriber {subscriber.msisdn} with error {e}")
                        pass
            else:
                answer.charging_rule_install.append(ChargingRuleInstall("PCRF_WITH_NO_SY_APPLICATION"))


            if self.rx_app:
                self.logger.debug(f"{__class__.__name__}✅ PCRF with Rx application")
                pass
            
                
        elif message.cc_request_type == E_CC_REQUEST_TYPE_UPDATE_REQUEST:
            self.logger.info(f"🔄 Gx CCR: Processing UPDATE request for session {message.session_id}")
            # Session lookup handled by SessionManager
            gx_session = self.get_session_by_id(message.session_id)
            if not gx_session:
                self.logger.error(f"{__class__.__name__}❌ Gx CCR: Session {message.session_id} not found for UPDATE request")
                raise ValueError(f"Session {message.session_id} not found")
            if message.rat_type and message.rat_type == E_RAT_TYPE_EUTRAN:
                answer.charging_rule_install.append(ChargingRuleInstall("EUTRAN_SERVICE"))
                answer.event_trigger.append(E_EVENT_TRIGGER_RAT_CHANGE)
            elif message.rat_type and message.rat_type == E_RAT_TYPE_GERAN:
                answer.charging_rule_install.append(ChargingRuleInstall("GERAN_SERVICE"))
                answer.event_trigger.append(E_EVENT_TRIGGER_RAT_CHANGE)
            elif message.rat_type and message.rat_type == E_RAT_TYPE_UTRAN:
                answer.charging_rule_install.append(ChargingRuleInstall("UTRAN_SERVICE"))
                answer.event_trigger.append(E_EVENT_TRIGGER_RAT_CHANGE)
            answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
            self.logger.info(f"{__class__.__name__}✅ Gx CCR: UPDATE request processed successfully for session {message.session_id}")
            
        elif message.cc_request_type == E_CC_REQUEST_TYPE_TERMINATION_REQUEST:
            self.logger.info(f"🛑 Gx CCR: Processing TERMINATION request for session {message.session_id}")
            # Session lookup and termination handled by SessionManager
            gx_session = self.get_session_by_id(message.session_id)
            if not gx_session:
                self.logger.error(f"{__class__.__name__}❌ Gx CCR: Session {message.session_id} not found for TERMINATION request")
                raise ValueError(f"Session {message.session_id} not found")
            answer.result_code = E_RESULT_CODE_DIAMETER_SUCCESS
            gx_session.end()
            self.logger.info(f"{__class__.__name__}✅ Gx CCR: TERMINATION request processed successfully for session {message.session_id}")
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

    def _handle_request(self, message: Message):
        answer = message.to_answer()
        answer.cc_request_number = message.cc_request_number
        answer.cc_request_type = message.cc_request_type
        return answer


from .. import Subscriber

class PcrfSyApplication(CommonThreadingApplication):
    MESSAGE_CREATE_SESSION = SLR
    MESSAGE_UPDATE_SESSION = None
    MESSAGE_TERMINATE_SESSION = SLR

    def __init__(self, max_threads: int = 1):
        super().__init__(application_id=APP_3GPP_SY, is_acct_application=False, is_auth_application=True, max_threads=max_threads)
        self.related_apps: List[CommonThreadingApplication] = []

    def create_session(self, subscriber: Subscriber) -> SySession:
        sy_session = SySession(self.node.session_generator.next_id(), subscriber=subscriber)
        self.session_manager.sessions.add_session(APP_3GPP_SY, sy_session)
        return sy_session

    def create_request(self, message_name: str, session: SySession) -> CreditControlRequest:
        if message_name == SLR:
            request = SpendingLimitRequest()
            request.header.application_id = APP_3GPP_SY
            request.session_id = session.session_id
            for k, v in self.avps.items():
                setattr(request, k, v)
            for k, v in session.avps.items():
                setattr(request, k, v)
            for k, v in session.subscriber.avps.items():
                setattr(request, k, v)
            return request
        elif message_name == SLR:
            pass
        return request
        
    def _handle_request(self, message: Message):
        answer = message.to_answer()
        answer.cc_request_number = message.cc_request_number
        answer.cc_request_type = message.cc_request_type
        return answer