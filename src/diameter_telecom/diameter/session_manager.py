from . import Subscriber
from .session import GxSession, RxSession, SySession, DiameterSession
from typing import Dict
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

    def __post_init__(self):
        # Ensure the main session dicts for each app_id are present
        self.sessions.setdefault(APP_3GPP_GX, dict())
        self.sessions.setdefault(APP_3GPP_RX, dict())
        self.sessions.setdefault(APP_3GPP_SY, dict())

    def stage_create_session(self, dm: DiameterMessage):
        app_id = dm.app_id
        session_id = dm.session_id
        # Ensure the app_id dict exists
        if app_id not in self.sessions:
            if app_id == APP_3GPP_GX:
                self.sessions[APP_3GPP_GX] = dict()
            elif app_id == APP_3GPP_RX:
                self.sessions[APP_3GPP_RX] = dict()
            elif app_id == APP_3GPP_SY:
                self.sessions[APP_3GPP_SY] = dict()
            else:
                self.sessions[app_id] = dict()
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
            self.stage_identify_subscriber(dm)
            self.stage_create_session(dm)

    def stage_parse_response(self, dm: DiameterMessage):
        app_id = dm.app_id
        session_id = dm.session_id
        if app_id in self.sessions and session_id in self.sessions[app_id]:
            self.sessions[app_id][session_id].add_message(dm)
            return self.sessions[app_id][session_id]
        else:
            # Optionally, handle the case where the session does not exist
            return None

    def process_diameter_message(self, dm: DiameterMessage):
        if dm.is_request:
            self.stage_parse_request(dm)
        else:
            self.stage_parse_response(dm)
