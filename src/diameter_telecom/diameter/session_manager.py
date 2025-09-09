from . import Subscriber
from .session import GxSession, RxSession, SySession, DiameterSession
from typing import List, Dict
from dataclasses import dataclass, field
import threading
from .constants import *
from .parse_avp import *
from .message import DiameterMessage


@dataclass
class Subscribers:
    subscribers: Dict[str, Subscriber] = field(default_factory=dict)

    def add_subscriber(self, subscriber: Subscriber):
        self.subscribers[subscriber.msisdn] = subscriber



@dataclass
class SessionManager:
    sessions: Dict[int, Dict[str, DiameterSession]] = field(default_factory=dict)
    subscribers: Subscribers = field(default_factory=Subscribers)
    messages: List[DiameterMessage] = field(default_factory=list)

    def __post_init__(self):
        # Ensure the main session dicts for each app_id are present
        self.sessions.setdefault(APP_3GPP_GX, dict())
        self.sessions.setdefault(APP_3GPP_RX, dict())
        self.sessions.setdefault(APP_3GPP_SY, dict())

    def get_messages(self):
        return sorted(self.messages, key=lambda x: x.timestamp if x.timestamp else float('inf'))

    def stage_create_session(self, dm: DiameterMessage):
        app_id = dm.app_id
        session_id = dm.session_id
        if dm.name not in [CCR_I, AAR, SLR]:
            return
        if app_id == APP_3GPP_GX:
            self.sessions[APP_3GPP_GX][session_id] = GxSession(session_id=session_id)
        elif app_id == APP_3GPP_RX:
            self.sessions[APP_3GPP_RX][session_id] = RxSession(session_id=session_id)
        elif app_id == APP_3GPP_SY:
            self.sessions[APP_3GPP_SY][session_id] = SySession(session_id=session_id)
        else:
            # Fallback: generic DiameterSession if unknown app_id
            self.sessions[app_id][session_id] = DiameterSession(session_id=session_id)
        self.sessions[app_id][session_id].add_message(dm)

    def stage_identify_subscriber(self, dm: DiameterMessage) -> Subscriber:
        if hasattr(dm.message, 'subscription_id') and dm.message.subscription_id:
            msisdn, imsi, sip_uri, nai, private_id = parse_subscription_id(dm.message.subscription_id)
            subscriber = Subscriber(msisdn=msisdn, imsi=imsi, sip_uri=sip_uri, nai=nai, private_id=private_id)
            self.subscribers.add_subscriber(subscriber)

    def stage_parse_request(self, dm: DiameterMessage):
            self.stage_create_session(dm)
            self.stage_identify_subscriber(dm)

    def stage_parse_response(self, dm: DiameterMessage):
        app_id = dm.app_id
        session_id = dm.session_id
        session = self.sessions[app_id].get(session_id)
        if not session:
            return
        session.add_message(dm)

    def process_diameter_message(self, dm: DiameterMessage):
        self.messages.append(dm)
        if dm.is_request:
            self.stage_parse_request(dm)
        else:
            self.stage_parse_response(dm)
  