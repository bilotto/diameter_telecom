# Services Architecture

> 🏗️ **Services provide the highest level of abstraction** and are the recommended way to work with diameter-telecom for most use cases.

## Overview

The Services layer sits above the entity layer and provides unified interfaces for common telecom scenarios. Services abstract away the complexity of managing multiple network entities and provide a clean, intuitive API for telecom operations.

## Service Layer Architecture

```
📊 Services Layer (High-Level API)
├─ DataService    → Data sessions (Gx + Sy)
├─ VoiceService   → Voice/media sessions (Gx + Rx)
└─ CustomService  → Your domain-specific logic

🔧 Entity Layer (Network Elements) 
├─ PCEF, PCRF, AF, OCS, DSC
└─ Direct Diameter application management

⚙️ Base Layer (diameter library)
└─ Core Diameter protocol implementation
```

## Available Services

### DataService
Manages data sessions across policy (Gx) and charging (Sy) interfaces.

**Key Features:**
- **Unified API**: Single `send_request()` handles both Gx and Sy messages
- **Automatic routing**: Messages routed to correct application based on app_id
- **Session coordination**: Links Gx policy sessions with Sy charging sessions
- **Host/realm management**: Automatically sets origin/destination headers

### VoiceService
Manages voice/media sessions across policy (Gx) and media (Rx) interfaces.

**Key Features:**
- **Gx-Rx coordination**: Links policy sessions with media reservations
- **IMS integration**: Handles P-CSCF scenarios with media control
- **QoS management**: Coordinates policy rules with media flows
- **Session binding**: Automatic Rx-to-Gx session association

## Service Benefits

### 🎯 Simplified Development
```python
# Without Services (manual entity management)
pcef.setup_gx_app()
pcef.start()
pcef.wait_for_ready()
gx_app = pcef.gx_app
answer = gx_app.send_request_custom(message)

# With Services (unified interface)  
data_service = DataService(pcef=pcef)
request, answer = data_service.send_request(message)
```

### ⚡ Automatic Configuration
- **Session Management**: Unified SessionManager across all applications
- **Message Headers**: Automatic origin/destination host/realm setting
- **Error Handling**: Consistent error handling and logging across services
- **Lifecycle Management**: Coordinated start/stop/wait_for_ready operations

### 📊 Production Features
- **Multi-threading**: Thread-safe operations across multiple applications
- **Performance Monitoring**: Built-in statistics and performance tracking
- **Configuration Management**: Centralized configuration for multiple entities
- **Extension Points**: Easy to extend with custom service logic

## DataService Usage

### Basic Setup
```python
from diameter_telecom import DataService, PCEF, OCS, SessionManager
from diameter_telecom.diameter.constants import APP_3GPP_GX

# 1. Create network entities
pcef = PCEF("pcef.mobile.net", "mobile.net", ["127.0.0.1"], tcp_port=3868)
ocs = OCS("ocs.billing.net", "billing.net", ["127.0.0.1"], tcp_port=3870)

# 2. Establish peer relationships
pcef.add_node_as_peer(pcrf.node, app_id=APP_3GPP_GX, initiate_connection=True)
ocs.add_node_as_peer(pcrf.node, app_id=APP_3GPP_SY, initiate_connection=False)

# 3. Setup applications and start entities
pcef.setup_gx_app()
ocs.setup_sy_app()
pcef.start()
ocs.start()

# 4. Create service
data_service = DataService(pcef=pcef, ocs=ocs)
data_service.set_session_manager(SessionManager())
```

### Sending Messages
```python
# Create subscriber and message
from diameter_telecom import Subscriber
subscriber = Subscriber(msisdn="1234567890", imsi="123456789012345")

# Send CCR (Credit Control Request) - automatically routes to Gx
ccr_message = create_ccr_initial_message(subscriber)
request, answer = data_service.send_request(ccr_message)

# Send SLR (Spending Limit Request) - automatically routes to Sy
slr_message = create_slr_message(subscriber)
request, answer = data_service.send_request(slr_message)
```

### Session Coordination
```python
# The service automatically coordinates sessions across applications
# Gx session for policy control
gx_session = data_service.get_gx_session(subscriber)

# Sy session for charging - automatically binds to Gx session
sy_session = data_service.get_sy_session(subscriber)
# sy_session.gx_session_id is automatically set
```

## VoiceService Usage

### Basic Setup
```python
from diameter_telecom import VoiceService, PCEF, AF
from diameter_telecom.diameter.constants import APP_3GPP_GX, APP_3GPP_RX

# 1. Create network entities
pcef = PCEF("pcef.mobile.net", "mobile.net", ["127.0.0.1"], tcp_port=3868)
af = AF("af.ims.net", "ims.net", ["127.0.0.1"], tcp_port=3871)

# 2. Establish peer relationships
pcef.add_node_as_peer(af.node, app_id=APP_3GPP_GX, initiate_connection=True)
af.add_node_as_peer(pcef.node, app_id=APP_3GPP_RX, initiate_connection=False)

# 3. Setup applications and start entities
pcef.setup_gx_app()
af.setup_rx_app()
pcef.start()
af.start()

# 4. Create service
voice_service = VoiceService(pcef=pcef, af=af)
voice_service.set_session_manager(SessionManager())
```

### IMS Voice Call Coordination
```python
# Policy reservation (Gx)
ccr_message = create_ccr_initial_message(subscriber)
gx_request, gx_answer = voice_service.send_request(ccr_message)

# Media reservation (Rx) - automatically coordinates with Gx session
aar_message = create_aar_message(subscriber)
rx_request, rx_answer = voice_service.send_request(aar_message)

# Sessions are automatically bound via framed IP addresses
```

## Service Configuration

### SessionManager Integration
```python
from diameter_telecom.diameter.session_manager import SessionManager

# Create centralized session manager
session_manager = SessionManager()

# Set on service
data_service.set_session_manager(session_manager)

# Access processed data
sessions = session_manager.sessions
subscribers = session_manager.subscribers
all_messages = session_manager.get_messages()
```

### Custom Service Logic
```python
from diameter_telecom.services.service import Service

class CustomService(Service):
    def __init__(self, pcef, custom_entity):
        super().__init__(pcef=pcef)
        self.custom_entity = custom_entity
    
    def send_request(self, message, timeout=10):
        # Custom routing logic
        if message.app_id == CUSTOM_APP_ID:
            return self.custom_entity.send_request(message, timeout)
        else:
            return super().send_request(message, timeout)
```

## Service Lifecycle

### Initialization
```python
# 1. Create entities
pcef = PCEF("pcef.example.com", "example.com")
ocs = OCS("ocs.example.com", "example.com")

# 2. Setup peer relationships
pcef.add_node_as_peer(ocs.node, app_id=APP_3GPP_GX)

# 3. Setup applications
pcef.setup_gx_app()
ocs.setup_sy_app()

# 4. Start entities
pcef.start()
ocs.start()

# 5. Create service
data_service = DataService(pcef=pcef, ocs=ocs)
```

### Message Processing
```python
# Send requests through service
request, answer = data_service.send_request(message, timeout=10)

# Service automatically:
# - Routes to correct application (Gx/Sy)
# - Sets proper headers
# - Manages session binding
# - Handles errors consistently
```

### Cleanup
```python
# Stop entities
pcef.stop()
ocs.stop()

# Service cleanup is automatic
```

## Best Practices

### 1. Use Services for Most Cases
```python
# ✅ Recommended: Use Services
data_service = DataService(pcef=pcef, ocs=ocs)
request, answer = data_service.send_request(message)

# ❌ Avoid: Direct entity management unless needed
pcef.setup_gx_app()
pcef.start()
# ... complex setup code
```

### 2. Leverage Automatic Routing
```python
# ✅ Let service handle routing
request, answer = data_service.send_request(message)
# Service automatically routes based on app_id

# ❌ Avoid: Manual routing unless necessary
if message.app_id == APP_3GPP_GX:
    answer = pcef.gx_app.send_request(message)
elif message.app_id == APP_3GPP_SY:
    answer = ocs.sy_app.send_request(message)
```

### 3. Use SessionManager for Centralized Control
```python
# ✅ Centralized session management
session_manager = SessionManager()
data_service.set_session_manager(session_manager)

# Access all data
sessions = session_manager.sessions
subscribers = session_manager.subscribers
```

## Common Patterns

### Multi-Service Network
```python
# Data service for data sessions
data_service = DataService(pcef=pcef, ocs=ocs)

# Voice service for voice sessions
voice_service = VoiceService(pcef=pcef, af=af)

# Both services can share the same PCEF
# Sessions are automatically coordinated
```

### Service Composition
```python
# Create custom service that combines multiple services
class MultiService:
    def __init__(self, data_service, voice_service):
        self.data_service = data_service
        self.voice_service = voice_service
    
    def send_request(self, message):
        if message.app_id in [APP_3GPP_GX, APP_3GPP_SY]:
            return self.data_service.send_request(message)
        elif message.app_id == APP_3GPP_RX:
            return self.voice_service.send_request(message)
```

## Next Steps

1. **Try Examples**: Check out the [comprehensive examples](../examples/data_service_comprehensive.md) to see Services in action
2. **Explore Entities**: Learn about [Network Entities](entities.md) for advanced control
3. **Session Management**: Understand [Session Management](sessions.md) for complex scenarios
4. **API Reference**: Explore the [API documentation](../api/services/data.md) for detailed class information
