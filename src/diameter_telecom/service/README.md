<!-- ApplicationService is a combination of CommonThreadingApplication objects sharing the same SessionManager, Subscribers and other attributes.
They can be used to represent the 3gpp roles, for instance:
- PCEF can be interpreted as ApplicationService with only PcefGxApplication
- PCRF can be interpreted as a ApplicationService with PcrfGxApplication, PcrfRxApplication, PcrfSyApplication
- Data Service can be PcefGxApplication + OcsSyApplication
- Voice Service with PcefGxApplication + AfRxApplication

They implement the methods
- create_session: delegates to the CommonThreadingApplication
- start_session
- update_session
- terminate_session


The ApplicationService class is responsible for creating the diameter requests.
It uses the AVP layering system

1- Application
2- Session
3- Service avps
4- Subscriber
5- AVPs from the user -->


# ApplicationService

`ApplicationService` composes multiple `CommonThreadingApplication`s sharing a `SessionManager` and `Subscribers`. It models 3GPP roles:

- PCEF: `PcefGxApplication`
- PCRF: `PcrfGxApplication` + `PcrfRxApplication` + `PcrfSyApplication`
- Data Service: `PcefGxApplication` + `OcsSyApplication`
- Voice Service: `PcefGxApplication` + `AfRxApplication`

Core methods:
- `create_session`, `start_session`, `update_session`, `terminate_session`, `refresh_session`

AVP layering applied to requests:
1) Application AVPs
2) Session AVPs
3) Service-level AVPs (by app id)
4) Subscriber AVPs