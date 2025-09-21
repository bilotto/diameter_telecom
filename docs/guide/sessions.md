# Session Management

Session management is at the heart of Diameter Telecom. The library provides sophisticated session handling with cross-application binding, lifecycle management, and optimized performance.

## Session Types

### GxSession (Policy Sessions)
Policy and charging control sessions between PCEF and PCRF.

**Key Features:**
- IP allocation management
- APN handling
- Charging rule management
- Policy enforcement

### RxSession (Media Sessions)
Media and application function sessions between PCRF and AF.

**Key Features:**
- Media resource management
- QoS control
- IMS integration
- Gx session binding

### SySession (Charging Sessions)
Spending limit and charging sessions between PCRF and OCS.

**Key Features:**
- Real-time charging
- Spending limit enforcement
- Credit management
- Gx session binding

## Session Lifecycle

### Session States
```
CREATED → ACTIVATED → TERMINATED
   ↓         ↓           ↓
Initial   Active    Cleanup
```

### Session Creation
```python
from diameter_telecom.diameter.session import GxSession, RxSession, SySession
from diameter_telecom import Subscriber

# Create subscriber
subscriber = Subscriber(msisdn="1234567890", imsi="123456789012345")

# Create Gx session
gx_session = GxSession(
    session_id="gx-12345",
    subscriber=subscriber,
    pcef_address="pcef.mobile.net",
    pcrf_address="pcrf.mobile.net"
)

# Create Rx session (automatically binds to Gx)
rx_session = RxSession(
    session_id="rx-67890",
    subscriber=subscriber,
    af_address="af.ims.net",
    pcrf_address="pcrf.mobile.net"
)
# rx_session.gx_session_id is automatically set

# Create Sy session (automatically binds to Gx)
sy_session = SySession(
    session_id="sy-54321",
    subscriber=subscriber,
    ocs_address="ocs.billing.net",
    pcrf_address="pcrf.mobile.net"
)
# sy_session.gx_session_id is automatically set
```

### Session Activation
```python
# Activate Gx session
gx_session.activate()
gx_session.state = SessionState.ACTIVATED

# Activate Rx session
rx_session.activate()
rx_session.state = SessionState.ACTIVATED

# Activate Sy session
sy_session.activate()
sy_session.state = SessionState.ACTIVATED
```

### Session Termination
```python
# Terminate sessions
gx_session.terminate()
rx_session.terminate()
sy_session.terminate()

# Cleanup is automatic
```

## Cross-Application Session Binding

### Automatic Binding
```python
# When creating Rx or Sy sessions, they automatically bind to active Gx sessions
subscriber = Subscriber(msisdn="1234567890", imsi="123456789012345")

# Gx session exists
gx_session = GxSession(session_id="gx-12345", subscriber=subscriber)
gx_session.activate()

# Rx session automatically binds to Gx
rx_session = RxSession(session_id="rx-67890", subscriber=subscriber)
# rx_session.gx_session_id = "gx-12345" (automatically set)

# Sy session automatically binds to Gx
sy_session = SySession(session_id="sy-54321", subscriber=subscriber)
# sy_session.gx_session_id = "gx-12345" (automatically set)
```

### Manual Binding
```python
# Manual binding when needed
rx_session.bind_to_gx_session(gx_session)
sy_session.bind_to_gx_session(gx_session)

# Check binding
if rx_session.gx_session_id:
    print(f"Rx session bound to Gx session: {rx_session.gx_session_id}")
```

### Binding Verification
```python
# Verify session binding
def verify_session_binding(session):
    if hasattr(session, 'gx_session_id') and session.gx_session_id:
        gx_session = get_session_by_id(session.gx_session_id)
        if gx_session and gx_session.state == SessionState.ACTIVATED:
            return True
    return False
```

## SessionManager Integration

### Centralized Session Management
```python
from diameter_telecom.diameter.session_manager import SessionManager

# Create session manager
session_manager = SessionManager()

# Process messages through the pipeline
diameter_message = DiameterMessage(hex_string_or_message_object)
session_manager.process_diameter_message(diameter_message)

# Access all sessions
gx_sessions = session_manager.get_sessions_by_type("GxSession")
rx_sessions = session_manager.get_sessions_by_type("RxSession")
sy_sessions = session_manager.get_sessions_by_type("SySession")

# Access sessions by subscriber
subscriber_sessions = session_manager.get_sessions_by_subscriber(subscriber)
```

### Session Retrieval
```python
# Get session by ID
session = session_manager.get_session_by_id("gx-12345")

# Get sessions by subscriber
subscriber_sessions = session_manager.get_sessions_by_subscriber(subscriber)

# Get active sessions
active_sessions = session_manager.get_active_sessions()

# Get sessions by type
gx_sessions = session_manager.get_sessions_by_type("GxSession")
```

### Session Statistics
```python
# Get session statistics
stats = session_manager.get_session_statistics()
print(f"Total sessions: {stats['total']}")
print(f"Active sessions: {stats['active']}")
print(f"Terminated sessions: {stats['terminated']}")

# Get sessions by application
gx_stats = session_manager.get_application_statistics("GxSession")
rx_stats = session_manager.get_application_statistics("RxSession")
sy_stats = session_manager.get_application_statistics("SySession")
```

## Session Data Management

### Session Attributes
```python
# Gx session attributes
gx_session.session_id = "gx-12345"
gx_session.subscriber = subscriber
gx_session.pcef_address = "pcef.mobile.net"
gx_session.pcrf_address = "pcrf.mobile.net"
gx_session.ip_address = "192.168.1.100"
gx_session.apn = "internet.mobile.net"
gx_session.charging_rules = ["rule1", "rule2"]
gx_session.state = SessionState.ACTIVATED

# Rx session attributes
rx_session.session_id = "rx-67890"
rx_session.subscriber = subscriber
rx_session.af_address = "af.ims.net"
rx_session.pcrf_address = "pcrf.mobile.net"
rx_session.media_info = {
    "codec": "AMR-WB",
    "bandwidth": "64kbps",
    "quality": "HD"
}
rx_session.gx_session_id = "gx-12345"  # Bound to Gx session

# Sy session attributes
sy_session.session_id = "sy-54321"
sy_session.subscriber = subscriber
sy_session.ocs_address = "ocs.billing.net"
sy_session.pcrf_address = "pcrf.mobile.net"
sy_session.charging_info = {
    "rate": 0.05,
    "currency": "USD",
    "limit": 100.00
}
sy_session.gx_session_id = "gx-12345"  # Bound to Gx session
```

### Session History
```python
# Access session message history
session_history = gx_session.get_message_history()
for message in session_history:
    print(f"Timestamp: {message.timestamp}")
    print(f"Command: {message.command_code}")
    print(f"Direction: {message.direction}")

# Get session context
context = gx_session.get_context()
print(f"Session context: {context}")
```

### Session Cleanup
```python
# Automatic cleanup on termination
gx_session.terminate()
# Session is automatically cleaned up

# Manual cleanup if needed
gx_session.cleanup()

# Bulk cleanup
session_manager.cleanup_terminated_sessions()
```

## Performance Optimization

### Direct Session Lookups
```python
# O(1) session access using subscriber tracking
subscriber = Subscriber(msisdn="1234567890", imsi="123456789012345")

# Direct lookup by application
gx_session = subscriber.session_ids.get("GxSession")
rx_session = subscriber.session_ids.get("RxSession")
sy_session = subscriber.session_ids.get("SySession")

# Check if session exists
if "GxSession" in subscriber.session_ids:
    gx_session = subscriber.session_ids["GxSession"]
```

### Session Caching
```python
# Session caching for performance
class SessionCache:
    def __init__(self):
        self._cache = {}
    
    def get_session(self, session_id):
        if session_id in self._cache:
            return self._cache[session_id]
        return None
    
    def cache_session(self, session_id, session):
        self._cache[session_id] = session
    
    def invalidate_session(self, session_id):
        if session_id in self._cache:
            del self._cache[session_id]
```

### Memory Management
```python
# Automatic memory cleanup
session_manager.cleanup_terminated_sessions()

# Manual memory management
session_manager.cleanup_stale_sessions(max_age=3600)  # 1 hour

# Memory usage monitoring
memory_stats = session_manager.get_memory_statistics()
print(f"Memory usage: {memory_stats['usage']} MB")
print(f"Session count: {memory_stats['session_count']}")
```

## Advanced Session Patterns

### Session Pooling
```python
class SessionPool:
    def __init__(self, max_sessions=1000):
        self.max_sessions = max_sessions
        self.sessions = {}
        self.available_sessions = []
    
    def get_session(self, session_type):
        if self.available_sessions:
            return self.available_sessions.pop()
        elif len(self.sessions) < self.max_sessions:
            return self.create_session(session_type)
        else:
            return None
    
    def return_session(self, session):
        session.reset()
        self.available_sessions.append(session)
```

### Session Replication
```python
class SessionReplicator:
    def __init__(self, primary_manager, backup_manager):
        self.primary = primary_manager
        self.backup = backup_manager
    
    def replicate_session(self, session):
        # Replicate session to backup
        self.backup.add_session(session)
    
    def failover(self):
        # Switch to backup manager
        return self.backup
```

### Session Persistence
```python
class PersistentSessionManager(SessionManager):
    def __init__(self, storage_backend):
        super().__init__()
        self.storage = storage_backend
    
    def save_session(self, session):
        # Save session to persistent storage
        self.storage.save_session(session)
    
    def load_session(self, session_id):
        # Load session from persistent storage
        return self.storage.load_session(session_id)
    
    def restore_sessions(self):
        # Restore all sessions from storage
        sessions = self.storage.load_all_sessions()
        for session in sessions:
            self.add_session(session)
```

## Best Practices

### 1. Use SessionManager for Centralized Control
```python
# ✅ Good: Centralized session management
session_manager = SessionManager()
session_manager.process_diameter_message(message)

# ❌ Avoid: Manual session management
sessions = {}
sessions[session_id] = session
```

### 2. Leverage Automatic Binding
```python
# ✅ Good: Let the library handle binding
rx_session = RxSession(session_id="rx-123", subscriber=subscriber)
# rx_session.gx_session_id is automatically set

# ❌ Avoid: Manual binding unless necessary
rx_session = RxSession(session_id="rx-123", subscriber=subscriber)
rx_session.gx_session_id = "gx-456"  # Manual binding
```

### 3. Use Direct Lookups for Performance
```python
# ✅ Good: Direct lookup
gx_session = subscriber.session_ids.get("GxSession")

# ❌ Avoid: Iterating through all sessions
for session in session_manager.sessions:
    if session.subscriber == subscriber and session.type == "GxSession":
        gx_session = session
        break
```

### 4. Clean Up Terminated Sessions
```python
# ✅ Good: Regular cleanup
session_manager.cleanup_terminated_sessions()

# ❌ Avoid: Accumulating terminated sessions
# Terminated sessions should be cleaned up regularly
```

## Common Patterns

### Multi-Application Session Coordination
```python
def coordinate_sessions(subscriber):
    # Get all sessions for subscriber
    sessions = session_manager.get_sessions_by_subscriber(subscriber)
    
    # Coordinate Gx and Rx sessions
    gx_session = sessions.get("GxSession")
    rx_session = sessions.get("RxSession")
    
    if gx_session and rx_session:
        # Ensure Rx session is bound to Gx session
        if not rx_session.gx_session_id:
            rx_session.bind_to_gx_session(gx_session)
        
        # Coordinate policy and media
        coordinate_policy_media(gx_session, rx_session)
    
    # Coordinate Gx and Sy sessions
    sy_session = sessions.get("SySession")
    if gx_session and sy_session:
        # Ensure Sy session is bound to Gx session
        if not sy_session.gx_session_id:
            sy_session.bind_to_gx_session(gx_session)
        
        # Coordinate policy and charging
        coordinate_policy_charging(gx_session, sy_session)
```

### Session Lifecycle Management
```python
def manage_session_lifecycle(session):
    # Session creation
    session.activate()
    
    # Session monitoring
    while session.state == SessionState.ACTIVATED:
        # Check session health
        if not session.is_healthy():
            session.terminate()
            break
        
        # Update session data
        session.update_data()
        
        # Sleep for monitoring interval
        time.sleep(30)
    
    # Session cleanup
    session.cleanup()
```

## Next Steps

1. **Try Examples**: Check out the [session examples](../examples/subscriber_session.md) to see session management in action
2. **Message Processing**: Understand [Message Processing](message_processing.md) for advanced scenarios
3. **Advanced Usage**: Explore [Advanced Usage](advanced.md) for custom implementations
4. **API Reference**: Explore the [API documentation](../api/session/session_manager.md) for detailed class information
