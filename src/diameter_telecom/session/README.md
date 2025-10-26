<!-- The DiameterSession represents a Gx, Rx, Sy, Gy session for the subscriber.

The session has a well defined lifecycle.
Each application has a different message that starts a session.
For example, Gx starts with CCR-I, Rx starts with AAR, Sy starts with SLR.
A session can be updated, refreshed and finally terminated.

The session object has different functions across the application. -->


A `DiameterSession` represents a Gx, Rx, or Sy session bound to a subscriber:
- Start: Gx → `CCR-I`, Rx → `AAR`, Sy → `SLR`
- Update/Refresh: application-specific messages
- Terminate: application-specific messages, handled via `ApplicationService`

Classes:
- `GxSession`, `RxSession`, `SySession` under `diameter_telecom.session`
- Managed by `SessionManager` (`diameter_telecom.session_manager`)