ApplicationService is a combination of CommonThreadingApplication objects sharing the same SessionManager, Subscribers and other attributes.
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