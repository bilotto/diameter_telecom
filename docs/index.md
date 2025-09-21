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

### High-Performance Processing Architecture
- **SessionManager**: Central orchestrator for message processing and data management
- **MessageProcessingPipeline**: Stage-based processing for optimal performance and maintainability
- **Optimized Session Binding**: Direct lookups using `subscriber.session_ids` for O(1) performance
- **Memory-Efficient**: Prompt cleanup and optimized data structures for telecom-scale throughput

### Telecom-Specific Applications
- **Gx Application**: Policy and Charging Control (PCRF-PCEF)
- **Rx Application**: Application Function (PCRF-AF)  
- **Sy Application**: Spending Limit Control (PCRF-OCS)

### Robust Message Handling
- **Safe AVP Parsing**: Bounds checking prevents crashes from malformed data
- **Comprehensive Message Support**: CCR/CCA, RAR/RAA, AAR/AAA, SLR/SLA, STR/STA
- **Error Resilience**: Graceful handling of malformed or incomplete Diameter messages
- **Message State Tracking**: Complete message lifecycle management

### Advanced Session Management
- **Cross-Application Binding**: Intelligent Sy-to-Gx and Rx-to-Gx session binding
- **Session Lifecycle**: Full state tracking (creation → activation → termination)
- **Subscriber Tracking**: Efficient session-to-subscriber association with cleanup
- **Message History**: Complete session message history and context preservation

### Enterprise-Grade Entity Management
- **3GPP Network Elements**: PCEF, PCRF, AF, OCS implementations
- **Subscriber Management**: MSISDN/IMSI-based identification and tracking
- **Carrier & APN Handling**: Comprehensive telecom network support
- **Service Layer**: Data and Voice service implementations

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

## Services Architecture

> 🏗️ **Services provide the highest level of abstraction** and are the recommended way to work with diameter-telecom for most use cases.

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
Manages data sessions across policy (Gx) and charging (Sy) interfaces with unified API and automatic routing.

### VoiceService
Manages voice/media sessions across policy (Gx) and media (Rx) interfaces with IMS integration.

## Key Components

### Core Processing Architecture
- **SessionManager**: The central orchestrator that manages all message processing, session storage, and subscriber tracking
- **MessageProcessingPipeline**: Handles stage-based message processing through discrete, testable stages
- **Sessions & Subscribers**: Optimized data management with efficient lookup patterns and memory cleanup

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

### 3GPP Network Entities
Production-ready implementations of telecom network elements:
- **PCEF**: Policy and Charging Enforcement Function (with Gx application)
- **PCRF**: Policy and Charging Rules Function (with Gx, Rx, Sy applications)
- **AF**: Application Function (with Rx application)
- **OCS**: Online Charging System (with Sy application)
- **DSC**: Diameter Signaling Controller for routing and load balancing

## Examples

The library includes comprehensive examples demonstrating real-world telecom scenarios:

### Comprehensive Examples
1. **Data Service Comprehensive** - Complete DataService usage with multiple carriers and subscriber scenarios
2. **Voice Service Comprehensive** - Complete VoiceService usage with IMS network simulation
3. **Multi-Service Advanced** - Advanced multi-service network with concurrent operations

### Basic Examples
4. **PCEF-PCRF Connection** - Simple PCEF-PCRF connection setup
5. **DSC Routing** - DSC-based routing demonstration
6. **Subscriber Management** - Carrier and subscriber setup

## Performance Features

- **Direct Session Lookups**: Uses `subscriber.session_ids[app_id]` for O(1) session access
- **Stage-Based Processing**: Breaks complex operations into discrete, optimized stages
- **Memory Management**: Automatic cleanup of terminated sessions and stale references
- **Safe AVP Parsing**: Bounds checking prevents crashes while maintaining performance

## Getting Started

1. **Installation**: See the [Installation Guide](setup.md) for setup instructions
2. **User Guide**: Start with the [Services Architecture](guide/services.md) for the recommended approach
3. **Examples**: Check out the [comprehensive examples](examples/data_service_comprehensive.md) to see real-world usage
4. **API Reference**: Explore the [API documentation](api/services/data.md) for detailed class information

## Acknowledgments

This library builds upon the base [diameter](https://github.com/mensonen/diameter) library, extending its functionality for telecommunications use cases.
