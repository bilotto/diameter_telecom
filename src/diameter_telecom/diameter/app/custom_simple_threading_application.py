from diameter.node.application import SimpleThreadingApplication
from ..message import DiameterMessage
from ..session._diameter_session import DiameterSession
from ..constants import *
from .. import Subscriber
from typing import Dict
import logging
logger = logging.getLogger(__name__)
import time
from ..session_manager import SessionManager

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
        self.session_manager = SessionManager()

    def remove_session(self, session_id):
        if session_id in self.sessions:
            del self.sessions[session_id]

    def add_subscriber(self, subscriber: Subscriber):
        if subscriber.msisdn in self.subscribers:
            return
        self.subscribers[subscriber.msisdn] = subscriber

    def send_request_custom(self, diameter_message: DiameterMessage, timeout=10):
        diameter_message.timestamp = time.time()
        self.session_manager.process_diameter_message(diameter_message)
        logger.info(f"\n{diameter_message.dump()}")
        answer = self.send_request(diameter_message.message, timeout=timeout)
        diameter_message_answer = DiameterMessage(answer)
        diameter_message_answer.timestamp = time.time()
        if diameter_message_answer.result_code != E_RESULT_CODE_DIAMETER_SUCCESS:
            logger.error(f"Answer with error: \n {diameter_message_answer}")
        logger.info(f"\n{diameter_message_answer.dump()}")
        self.session_manager.process_diameter_message(diameter_message_answer)
        return diameter_message_answer