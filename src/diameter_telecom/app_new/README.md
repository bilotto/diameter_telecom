All applications share common class CommonThreadingApplication that comes from ThreadingApplication (diameter module)


All applications need to have the methods:
- handle_request
- create_request
- create_session

They can be used alone with their own session_manager
The apps can send requests through common method send_request_custom that uses session_manager