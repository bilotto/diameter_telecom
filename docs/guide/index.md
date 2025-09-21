# User Guide

Welcome to the Diameter Telecom user guide! This guide will help you understand the architecture and learn how to use the library effectively.

## Architecture Overview

Diameter Telecom is built on a layered architecture that provides different levels of abstraction:

```
📊 Services Layer (Recommended)
├─ DataService    → High-level data session management
├─ VoiceService   → High-level voice/media session management
└─ CustomService → Your domain-specific services

🔧 Entity Layer (Network Elements)
├─ PCEF, PCRF, AF, OCS, DSC
└─ Direct Diameter application management

⚙️ Base Layer (diameter library)
└─ Core Diameter protocol implementation
```

## Getting Started Paths

### 🚀 Quick Start (Recommended)
If you want to get up and running quickly with minimal configuration:

1. **Start with Services**: Begin with [Services Architecture](services.md) to understand the high-level approach
2. **Try Examples**: Run the [comprehensive examples](examples/data_service_comprehensive.md) to see real-world usage
3. **Explore API**: Check the [API Reference](../api/services/data.md) for detailed documentation

### 🔧 Advanced Usage
If you need fine-grained control or are building custom solutions:

1. **Entity Management**: Learn about [Network Entities](entities.md) for direct control
2. **Session Management**: Understand [Session Management](sessions.md) for advanced scenarios
3. **Message Processing**: Dive into [Message Processing](message_processing.md) for custom logic

## Key Concepts

### Services-First Approach
The library is designed around a **Services-First** philosophy:

- **Services** provide the highest level of abstraction and are recommended for most use cases
- **Entities** provide direct control over network elements when needed
- **Base Layer** handles the low-level Diameter protocol details

### Session Management
All telecom operations revolve around sessions:

- **Gx Sessions**: Policy and charging control sessions
- **Rx Sessions**: Media and application function sessions  
- **Sy Sessions**: Spending limit and charging sessions
- **Cross-Application Binding**: Sessions automatically bind across applications

### Message Processing Pipeline
The library uses a sophisticated message processing pipeline:

1. **Session Retrieval**: Find or create appropriate sessions
2. **Subscriber Identification**: Identify the subscriber from message data
3. **Cross-Application Binding**: Link sessions across different applications
4. **Business Logic**: Apply application-specific processing

## Guide Sections

### [Services Architecture](services.md)
Learn about the high-level Services layer that provides unified interfaces for common telecom scenarios.

### [Network Entities](entities.md)
Understand the 3GPP network element implementations (PCEF, PCRF, AF, OCS, DSC).

### [Session Management](sessions.md)
Master the session lifecycle and cross-application session binding.

### [Message Processing](message_processing.md)
Dive into the message processing pipeline and custom processing logic.

### [Advanced Usage](advanced.md)
Explore advanced features, performance optimization, and custom implementations.

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

### 2. Leverage Session Binding
```python
# ✅ Automatic cross-application binding
sy_session = SySession(session_id="sy-123", subscriber=subscriber)
# sy_session.gx_session_id is automatically set

# ✅ Manual binding when needed
sy_session.bind_to_gx_session(gx_session)
```

### 3. Use SessionManager for Centralized Control
```python
# ✅ Centralized session management
session_manager = SessionManager()
session_manager.process_diameter_message(message)

# Access all data
sessions = session_manager.sessions
subscribers = session_manager.subscribers
```

## Common Patterns

### Basic Service Usage
```python
from diameter_telecom import DataService, PCEF, OCS

# Create entities
pcef = PCEF("pcef.example.com", "example.com")
ocs = OCS("ocs.example.com", "example.com")

# Create service
data_service = DataService(pcef=pcef, ocs=ocs)

# Send messages
request, answer = data_service.send_request(ccr_message)
```

### Advanced Entity Management
```python
from diameter_telecom.entities_3gpp import PCRF, PCEF
from diameter_telecom.diameter.constants import APP_3GPP_GX

# Create entities
pcrf = PCRF("pcrf.example.com", "example.com")
pcef = PCEF("pcef.example.com", "example.com")

# Setup peer relationships
pcrf.add_node_as_peer(pcef.node, app_id=APP_3GPP_GX)
pcef.add_node_as_peer(pcrf.node, app_id=APP_3GPP_GX)

# Setup applications
pcrf.setup_gx_app()
pcef.setup_gx_app()

# Start entities
pcrf.start()
pcef.start()
```

## Next Steps

1. **Choose your path**: Services (recommended) or Entities (advanced)
2. **Read the relevant guide section**: Start with [Services Architecture](services.md)
3. **Try the examples**: Run the [comprehensive examples](../examples/data_service_comprehensive.md)
4. **Explore the API**: Check the [API Reference](../api/services/data.md) for detailed documentation

## Need Help?

- **Examples**: Check the [Examples section](../examples/data_service_comprehensive.md) for working code
- **API Reference**: Explore the [API documentation](../api/services/data.md) for detailed class information
- **GitHub Issues**: Report issues or ask questions on [GitHub](https://github.com/bilotto/diameter_telecom/issues)
