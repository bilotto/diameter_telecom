# Diameter Telecom

A Python library for implementing Diameter protocol applications in telecommunications networks, built on top of the base [diameter](https://github.com/mensonen/diameter) library.

## Overview

Diameter Telecom brings telecom intelligence to the powerful but low-level diameter library — letting you simulate real PCRF/PCEF nodes, manage sessions, and handle AVPs with ease. It provides a high-level interface for implementing and managing Diameter applications in telecommunications networks, making it simple to build, simulate, and integrate telecom-grade Diameter flows.

## Architecture

Diameter Telecom extends the base diameter library with telecom-specific functionality:

- **Base Layer**: Uses the [diameter](https://github.com/mensonen/diameter) library for core Diameter protocol implementation
- **Processing Layer**: High-performance message processing with:
  - **SessionManager**: Centralized orchestration of message processing and data management
  - **MessageProcessingPipeline**: Stage-based processing for scalability and maintainability
  - **Optimized Session Binding**: Direct lookups using subscriber tracking for performance
- **Telecom Layer**: Adds telecom-specific features like:
  - 3GPP network element implementations (PCRF, PCEF, AF, OCS)
  - Telecom-specific message handling and parsing
  - Advanced session management for Gx, Rx, and Sy applications
  - Subscriber and carrier management with intelligent session tracking

## Features

- **High-Performance Processing Architecture**
  - **SessionManager**: Central orchestrator for message processing and data management
  - **MessageProcessingPipeline**: Stage-based processing for optimal performance and maintainability
  - **Optimized Session Binding**: Direct lookups using `subscriber.session_ids` for O(1) performance
  - **Memory-Efficient**: Prompt cleanup and optimized data structures for telecom-scale throughput

- **Telecom-Specific Applications**
  - **Gx Application**: Policy and Charging Control (PCRF-PCEF)
  - **Rx Application**: Application Function (PCRF-AF)  
  - **Sy Application**: Spending Limit Control (PCRF-OCS)

- **Robust Message Handling**
  - **Safe AVP Parsing**: Bounds checking prevents crashes from malformed data
  - **Comprehensive Message Support**: CCR/CCA, RAR/RAA, AAR/AAA, SLR/SLA, STR/STA
  - **Error Resilience**: Graceful handling of malformed or incomplete Diameter messages
  - **Message State Tracking**: Complete message lifecycle management

- **Advanced Session Management**
  - **Cross-Application Binding**: Intelligent Sy-to-Gx and Rx-to-Gx session binding
  - **Session Lifecycle**: Full state tracking (creation → activation → termination)
  - **Subscriber Tracking**: Efficient session-to-subscriber association with cleanup
  - **Message History**: Complete session message history and context preservation

- **Enterprise-Grade Entity Management**
  - **3GPP Network Elements**: PCEF, PCRF, AF, OCS implementations
  - **Subscriber Management**: MSISDN/IMSI-based identification and tracking
  - **Carrier & APN Handling**: Comprehensive telecom network support
  - **Service Layer**: Data and Voice service implementations

### Additional Capabilities

- ✅ Automatic response generation for CCR/RAR flows
- ✅ Plug-and-play request handlers for each 3GPP application
- ✅ Seamless integration with base diameter library's TCP and SCTP support

## Installation

Since this package is not yet available on PyPI, you'll need to install it from the source:

```bash
git clone https://github.com/bilotto/diameter_telecom.git
cd diameter_telecom
pip install -r requirements.txt
pip install -e .
```

## Dependencies

- diameter (base library)
- Python 3.10+

## Quick Start

> ⚡ **The recommended way to use diameter-telecom is through the Services layer**, which provides high-level abstractions over network entities and handles message routing automatically.

### Services-First Approach (Recommended)

```python
from diameter_telecom import PCEF, PCRF, OCS, DataService, SessionManager
from diameter_telecom.diameter.constants import APP_3GPP_GX

# 1. Create and setup network entities
pcef = PCEF("pcef.mobile.net", "mobile.net", ["127.0.0.1"], tcp_port=3868)
pcrf = PCRF("pcrf.mobile.net", "mobile.net", ["127.0.0.1"], tcp_port=3869) 
ocs = OCS("ocs.billing.net", "billing.net", ["127.0.0.1"], tcp_port=3870)

# 2. Establish peer relationships
pcef.add_node_as_peer(pcrf.node, app_id=APP_3GPP_GX, initiate_connection=True)
pcrf.add_node_as_peer(pcef.node, app_id=APP_3GPP_GX, initiate_connection=False)

# 3. Setup applications and start entities
pcef.setup_gx_app()
pcrf.setup_gx_app() 
pcef.start()
pcrf.start()

# 4. Create high-level service (automatically handles message routing)
data_service = DataService(pcef=pcef, ocs=ocs)
data_service.set_session_manager(SessionManager())

# 5. Send messages through unified service API
from diameter_telecom import Subscriber, DiameterMessage
subscriber = Subscriber(msisdn="1234567890", imsi="123456789012345")
ccr_message = create_ccr_initial_message(subscriber)
request, answer = data_service.send_request(ccr_message)
```

### Direct Entity Usage (Advanced)

```python
from diameter_telecom.entities_3gpp import PCRF, PCEF

# For advanced use cases requiring direct entity control
pcrf = PCRF("pcrf.python.realm", "python.realm", ["127.0.0.1"], tcp_port=3868)
pcef = PCEF("pcef.python.realm", "python.realm", ["127.0.0.1"], tcp_port=3869)

# Manual setup required
pcrf.add_node_as_peer(pcef.node, app_id=APP_3GPP_GX, initiate_connection=False)
pcef.add_node_as_peer(pcrf.node, app_id=APP_3GPP_GX, initiate_connection=True)
pcrf.setup_gx_app()
pcef.setup_gx_app()
pcrf.start()
pcef.start()
```

## Before & After: Simplified API

### Before: Complex PCRF-PCEF Connection Setup

The base diameter library requires significant boilerplate code to set up even a simple PCRF-PCEF connection. Here's what you need to do:

```python
from diameter.node import Node
from diameter.node.application import SimpleThreadingApplication
from diameter.message.constants import APP_3GPP_GX

def handle_request_gx():
  # Implementation needed
  pass

# Create nodes
pcrf = Node(origin_host="pcrf.python.realm", realm_name="python.realm")
pcrf.ip_addresses=["127.0.0.1"]
pcrf.tcp_port=3868
pcrf.vendor_ids=[10415]

pcef = Node(origin_host="pcef.python.realm", realm_name="python.realm")
pcef.ip_addresses=["127.0.0.1"]
pcef.tcp_port=3869
pcef.vendor_ids=[10415]

# Create applications
gx_pcrf_app = SimpleThreadingApplication(
    application_id=APP_3GPP_GX,
    is_acct_application=False,
    is_auth_application=True,
    max_threads=1,
    request_handler=handle_request_gx
)
gx_pcef_app = SimpleThreadingApplication(
    application_id=APP_3GPP_GX,
    is_acct_application=False,
    is_auth_application=True,
    max_threads=1,
    request_handler=handle_request_gx
)

# Add applications and peers
pcrf.add_application(gx_pcrf_app, [
    pcrf.add_peer(
        f"aaa://{pcef.origin_host}:{pcef.tcp_port};transport=tcp",
        pcef.realm_name,
        ip_addresses=pcef.ip_addresses,
        is_persistent=False
    )
])
pcef.add_application(gx_pcef_app, [
    pcef.add_peer(
        f"aaa://{pcrf.origin_host}:{pcrf.tcp_port};transport=tcp",
        pcrf.realm_name,
        ip_addresses=pcrf.ip_addresses,
        is_persistent=True
    )
])

# Start nodes
pcrf.start()
pcef.start()
```

This complex setup requires:
- Manual node configuration
- Explicit application creation and configuration
- Complex peer connection setup
- Manual request handler implementation
- Careful management of vendor IDs and application types

Diameter Telecom simplifies all of this into a clean, intuitive API as shown in the Quick Start section above.

### Built-in Request Handlers

The library provides pre-implemented request handlers for common Diameter applications:

- **handle_request_gx**: Handles Gx application requests
- **handle_request_rx**: Handles Rx application requests
- **handle_request_sy**: Handles Sy application requests

These handlers are automatically configured when using the entity classes (PCRF, PCEF, etc.), eliminating the need to manually set up request handling logic.

## Key Components

### Core Processing Architecture

- **SessionManager**: The central orchestrator that manages all message processing, session storage, and subscriber tracking. Delegates processing logic to MessageProcessingPipeline while maintaining high-level data management.

- **MessageProcessingPipeline**: Handles stage-based message processing through discrete, testable stages:
  - Session retrieval and creation
  - Subscriber identification and management  
  - Cross-application session binding
  - Application-specific business logic

- **Sessions & Subscribers**: Optimized data management with efficient lookup patterns and memory cleanup.

### Diameter Applications

The library provides complete implementations for 3GPP Diameter applications:

- **GxApplication**: Policy and Charging Control (PCRF ↔ PCEF)
- **RxApplication**: Application Function (PCRF ↔ AF)  
- **SyApplication**: Spending Limit Control (PCRF ↔ OCS)

### Session Management

Advanced session handling through specialized session classes:

- **GxSession**: Policy sessions with IP allocation, APN, and charging rule management
- **RxSession**: Media sessions with Gx session binding for coordinated policy control
- **SySession**: Spending limit sessions with Gx session binding for integrated charging

Key features:
- **Cross-application binding**: Sy and Rx sessions automatically bind to related Gx sessions
- **Optimized lookups**: Direct session access via `subscriber.session_ids` dictionary  
- **Lifecycle management**: Complete session state tracking with automatic cleanup

### 3GPP Network Entities

Production-ready implementations of telecom network elements:

- **PCEF**: Policy and Charging Enforcement Function (with Gx application)
- **PCRF**: Policy and Charging Rules Function (with Gx, Rx, Sy applications)
- **AF**: Application Function (with Rx application)
- **OCS**: Online Charging System (with Sy application)
- **DSC**: Diameter Signaling Controller for routing and load balancing

## Services Architecture

> 🏗️ **Services provide the highest level of abstraction** and are the recommended way to work with diameter-telecom for most use cases.

### Service Layer Overview

The Services layer sits above the entity layer and provides unified interfaces for common telecom scenarios:

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

### DataService

Manages data sessions across policy (Gx) and charging (Sy) interfaces:

```python
from diameter_telecom import DataService, PCEF, OCS

# Service composes multiple entities
data_service = DataService(pcef=pcef, ocs=ocs)

# Unified message sending across multiple applications
request, answer = data_service.send_request(ccr_message)
# ↳ Automatically routes to Gx or Sy based on message type
```

**Key Features:**
- **Unified API**: Single `send_request()` handles both Gx and Sy messages
- **Automatic routing**: Messages routed to correct application based on app_id
- **Session coordination**: Links Gx policy sessions with Sy charging sessions
- **Host/realm management**: Automatically sets origin/destination headers

### VoiceService

Manages voice/media sessions across policy (Gx) and media (Rx) interfaces:

```python
from diameter_telecom import VoiceService, PCEF, AF

# Service handles IMS voice call coordination
voice_service = VoiceService(pcef=pcef, af=af)

# Coordinates both policy and media reservations
gx_req, gx_ans = voice_service.send_request(ccr_message)  # Policy
rx_req, rx_ans = voice_service.send_request(aar_message)  # Media
# ↳ Sessions automatically bound via framed IP addresses
```

**Key Features:**
- **Gx-Rx coordination**: Links policy sessions with media reservations
- **IMS integration**: Handles P-CSCF scenarios with media control
- **QoS management**: Coordinates policy rules with media flows
- **Session binding**: Automatic Rx-to-Gx session association

### Service Benefits

**🎯 Simplified Development:**
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

**⚡ Automatic Configuration:**
- **Session Management**: Unified SessionManager across all applications
- **Message Headers**: Automatic origin/destination host/realm setting
- **Error Handling**: Consistent error handling and logging across services
- **Lifecycle Management**: Coordinated start/stop/wait_for_ready operations

**📊 Production Features:**
- **Multi-threading**: Thread-safe operations across multiple applications
- **Performance Monitoring**: Built-in statistics and performance tracking
- **Configuration Management**: Centralized configuration for multiple entities
- **Extension Points**: Easy to extend with custom service logic

## Advanced Usage

### SessionManager Integration

For applications requiring centralized session management and message processing:

```python
from diameter_telecom.diameter.session_manager import SessionManager
from diameter_telecom.diameter.message import DiameterMessage

# Create centralized session manager
session_manager = SessionManager()

# Process messages through the pipeline
diameter_message = DiameterMessage(hex_string_or_message_object)
session_manager.process_diameter_message(diameter_message)

# Access processed data
sessions = session_manager.sessions
subscribers = session_manager.subscribers
all_messages = session_manager.get_messages()  # Sorted by timestamp
```

### Service Layer Usage

For complete telecom service implementations:

```python
from diameter_telecom.services import DataService
from diameter_telecom.entities_3gpp import PCEF, OCS

# Create entities
pcef = PCEF(origin_host="pcef.example.com", realm_name="example.com")
ocs = OCS(origin_host="ocs.example.com", realm_name="example.com")

# Create service with multiple entities
data_service = DataService(pcef=pcef, ocs=ocs)

# Automatic session manager integration
data_service.set_session_manager()  # Creates shared SessionManager

# Send requests through service layer
request = create_ccr_initial()  # Your message creation
response = data_service.send_request(request, timeout=10)
```

### Performance Optimization

The library implements several performance optimizations:

1. **Direct Session Lookups**: Uses `subscriber.session_ids[app_id]` for O(1) session access
2. **Stage-Based Processing**: Breaks complex operations into discrete, optimized stages
3. **Memory Management**: Automatic cleanup of terminated sessions and stale references
4. **Safe AVP Parsing**: Bounds checking prevents crashes while maintaining performance

### Session Binding Patterns

The library automatically handles cross-application session binding:

```python
# When creating Sy session, it automatically binds to active Gx session
sy_session = SySession(session_id="sy-123", subscriber=subscriber)
# sy_session.gx_session_id is automatically set if Gx session exists

# Same for Rx sessions  
rx_session = RxSession(session_id="rx-456", subscriber=subscriber)
# rx_session.gx_session_id is automatically set based on subscriber tracking
```

## Examples

The library includes comprehensive examples demonstrating real-world telecom scenarios:

### Comprehensive Examples

1. **`data_service_comprehensive.py`** - Complete DataService usage
   - Multiple carriers with different APNs (internet, premium, IoT)
   - 5 different subscriber scenarios (regular, premium, IoT, heavy usage, roaming)
   - Full session lifecycle (Initial → Updates → Termination)
   - PCEF-PCRF-OCS integration with Gx/Sy coordination

2. **`voice_service_comprehensive.py`** - Complete VoiceService usage
   - IMS network simulation with PCEF-PCRF-AF entities
   - Voice call scenarios (voice, video, HD video, conference)
   - Gx-Rx session binding and media resource management
   - Real-world IMS call flows and modifications

3. **`multi_service_advanced.py`** - Advanced multi-service network
   - Concurrent DataService and VoiceService operations
   - Multiple carriers (European, American, Asian) with realistic subscriber bases
   - Performance simulation with 45+ subscribers and concurrent sessions
   - Network-wide statistics and performance monitoring

### Basic Examples

4. **`pcef_pcrf_connection.py`** - Simple PCEF-PCRF connection
   - Basic entity setup and message sending
   - Shows direct entity usage (advanced pattern)

5. **`pcef_pcrf_with_dsc.py`** - DSC-based routing
   - Demonstrates DSC as Diameter Signaling Controller
   - Multi-entity coordination through DSC

6. **`subscriber_session.py`** - Subscriber management
   - Carrier and subscriber setup
   - APN assignment and session initialization

### Running Examples

```bash
# Services-based examples (recommended)
python examples/data_service_comprehensive.py
python examples/voice_service_comprehensive.py
python examples/multi_service_advanced.py

# Entity-based examples (advanced usage)
python examples/pcef_pcrf_connection.py
python examples/pcef_pcrf_with_dsc.py
```

> 💡 **Start with the comprehensive examples** to see the Services architecture in action. They demonstrate real-world telecom scenarios and best practices.

## Acknowledgments

This library builds upon the base [diameter](https://github.com/mensonen/diameter) library, extending its functionality for telecommunications use cases. 


