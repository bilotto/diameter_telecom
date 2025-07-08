# Diameter Telecom

A Python library for implementing Diameter protocol applications in telecommunications networks, built on top of the base [diameter](https://github.com/mensonen/diameter) library.

## Overview

Diameter Telecom brings telecom intelligence to the powerful but low-level diameter library — letting you simulate real PCRF/PCEF nodes, manage sessions, and handle AVPs with ease. It provides a high-level interface for implementing and managing Diameter applications in telecommunications networks, making it simple to build, simulate, and integrate telecom-grade Diameter flows.

## Architecture

Diameter Telecom extends the base diameter library with telecom-specific functionality:

- **Base Layer**: Uses the [diameter](https://github.com/mensonen/diameter) library for core Diameter protocol implementation
- **Telecom Layer**: Adds telecom-specific features like:
  - 3GPP network element implementations (PCRF, PCEF, AF)
  - Telecom-specific message handling and parsing
  - Session management for different Diameter applications
  - Subscriber and carrier management

## Features

- **Telecom-Specific Applications**
  - Gx Application: Policy and Charging Control
  - Rx Application: Application Function
  - Sy Application: Spending Limit Control

- **Enhanced Message Handling**
  - Telecom-specific message parsing and formatting
  - Support for various Diameter message types (CCR/CCA, RAR/RAA, etc.)
  - Subscriber information management
  - Session tracking and management

- **Entity Management**
  - Support for 3GPP network elements (PCEF, PCRF, AF)
  - Carrier and subscriber management
  - APN (Access Point Name) handling

- **Session Management**
  - Per-application session tracking with message history and subscriber context
  - Message history and state management
  - Subscriber association with sessions

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

### Applications

The library provides implementations for three main Diameter applications:

- **Gx Application**: Used for Policy and Charging Control
- **Rx Application**: Used for Application Function
- **Sy Application**: Used for Spending Limit Control

### Sessions

Session management is handled through specialized session classes:

- GxSession: Manages Gx application sessions
- RxSession: Manages Rx application sessions
- SySession: Manages Sy application sessions

### Entities

The library includes implementations for common 3GPP network elements:

- PCEF: Policy and Charging Enforcement Function
- PCRF: Policy and Charging Rules Function
- AF: Application Function

## Acknowledgments

This library builds upon the base [diameter](https://github.com/mensonen/diameter) library, extending its functionality for telecommunications use cases. 


