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

Here's a simple example of setting up a PCRF-PCEF connection:

```python
from diameter_telecom.entities_3gpp import PCRF, PCEF

# Create PCRF and PCEF nodes
pcrf = PCRF(
    origin_host="pcrf.python.realm",
    realm_name="python.realm",
    ip_addresses=["127.0.0.1"],
    tcp_port=3868
)
pcef = PCEF(
    origin_host="pcef.python.realm",
    realm_name="python.realm",
    ip_addresses=["127.0.0.1"],
    tcp_port=3869
)

# Connect nodes
pcrf.add_peer(pcef, initiate_connection=False)
pcef.add_peer(pcrf, initiate_connection=True)

# Start nodes
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

## Acknowledgments

This library builds upon the base [diameter](https://github.com/mensonen/diameter) library, extending its functionality for telecommunications use cases. 


