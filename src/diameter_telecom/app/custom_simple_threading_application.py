from diameter.node.application import SimpleThreadingApplication
from ..diameter_message import DiameterMessage
from ..diameter_session import DiameterSession
from ..subscriber import Subscriber
from ..constants import *
from typing import Dict
import logging
from diameter.message import dump

logger = logging.getLogger(__name__)

class CustomSimpleThreadingApplication(SimpleThreadingApplication):
    def __init__(self, application_id,
                 is_acct_application,
                 is_auth_application,
                 max_threads,
                 request_handler,
                 ):
        super().__init__(application_id, is_acct_application, is_auth_application, max_threads, request_handler)
        self.sessions: Dict[str, DiameterSession] = {}
        self.subscribers: Dict[str, Subscriber] = {}

    def remove_session(self, session_id):
        if session_id in self.sessions:
            del self.sessions[session_id]

    def send_request_custom(self, diameter_message: DiameterMessage, timeout=10):
        answer = self.send_request(diameter_message.message, timeout=timeout)
        if answer.result_code != E_RESULT_CODE_DIAMETER_SUCCESS:
            logger.error(f"Answer with error: \n {dump(answer)}")
        return answer

    # def send_request_custom(self, request, timeout=5):
    #     # print(request)
    #     session_id = request.session_id
    #     session = self.get_session_by_id(session_id)
    #     if not session:
    #         # raise Exception(f"Session {session_id} not found. Add to the session store before sending request")
    #         logger.error(f"Session {session_id} not found. Add to the session store before sending request")
    #         return None
    #     session.add_message(request)
    #     try:
    #         answer = self.send_request(request, timeout)
    #     except Exception as e:
    #         self.stats.increment_transaction_count(success=False)
    #         logger.error(f"Error sending request: {e}")
    #         raise e
    #     #
    #     session.add_message(answer)
    #     self.stats.increment_based_on_answer(answer)
    #     result_code = answer.result_code
    #     self.stats.increment_rc_count(result_code)
    #     # self.stats.increment_request_count(success=True)
    #     return answer

        
    # def set_subscribers(self, subscribers: Subscribers):
    #     for i in subscribers.values():
    #         self.subscribers.add_subscriber(i)

    # def add_subscriber(self, subscriber: Subscriber):
    #     self.subscribers.add_subscriber(subscriber)

    # def get_session_by_id(self, session_id: str) -> DiameterSession:
    #     return self.sessions.get_session(session_id)
    
    # def get_subscriber_active_session_by_msisdn(self, msisdn: int) -> DiameterSession:
    #     active_sessions = []
    #     if self.get_msisdn_sessions(msisdn):
    #         for session in self.get_msisdn_sessions(msisdn):
    #             if session.active:
    #                 active_sessions.append(session)
    #     if not active_sessions:
    #         return None
    #     if len(active_sessions) > 1:
    #         logger.warning(f"More than one active session found for MSISDN {msisdn}")

    
    # def get_subscriber_sessions_by_msisdn(self, msisdn: int):
    #     return self.sessions.get_msisdn_sessions(msisdn)
    
    # def get_subscriber_active_session(self, msisdn: int):
    #     if self.sessions.get_msisdn_sessions(msisdn):
    #         for session in self.sessions.get_msisdn_sessions(msisdn):
    #             if session.active:
    #                 return session

    # def create_session(self, session_id: str, subscriber: Subscriber):
    #     return self.sessions.create_diameter_session(session_id, subscriber)