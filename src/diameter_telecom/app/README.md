<!-- All applications share common class CustomSimpleThreadingApplication that comes from SimpleThreadingApplication (diameter module)

The difference from the CommonThreadingApplication is that the handle_request method comes from an external function that the user can pass.

Right now we are only using these applications for the DSC. The DSC provides the handle_request_dsc as the handle_request method.

 -->

`CustomSimpleThreadingApplication` extends `diameter.node.application.SimpleThreadingApplication` and accepts an external `request_handler`. This is ideal when routing/handling logic lives outside the app class (e.g., DSC).

By contrast, `app_new.CommonThreadingApplication` uses a template method: the app implements `_handle_request`, and the framework wraps request/answer processing through the `SessionManager`.

Current usage: DSC injects `handle_request_dsc` (`diameter_telecom.entities_3gpp.dsc.handle_request_dsc`) when creating apps.

When to use:
- `CustomSimpleThreadingApplication`: external handler, lightweight, routing scenarios (DSC).
- `CommonThreadingApplication`: cohesive app behavior, lifecycle + AVP layering, full session integration.