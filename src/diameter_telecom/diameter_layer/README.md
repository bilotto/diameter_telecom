<!-- This is suppose to be a layer where we get all the objects we need from the diameter library.
And then the rest of the application will import from here.
But this is not happening in the code right now.
Is it a good idea? -->

# Diameter Layer

This layer is the façade over the upstream `diameter` library and local helpers. Import Diameter primitives and helpers from here to keep the rest of the code decoupled from the upstream library.

Provides:
- `Node`, `Peer` (`diameter_telecom.diameter_layer.helpers`)
- Request handlers/dispatchers (`diameter_telecom.diameter_layer.handle_request.*`)
- AVP parsing and JSON utils (`parse_avp`, `json_utils`)

Guideline: Applications and services should import Diameter-facing types via this layer.