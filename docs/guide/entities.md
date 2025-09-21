# Network Entities

The Entity layer provides direct control over 3GPP network elements. While Services are recommended for most use cases, entities give you fine-grained control when needed.

## Available Entities

### PCEF (Policy and Charging Enforcement Function)
The PCEF enforces policy and charging rules at the network edge.

**Applications:**
- Gx Application (Policy and Charging Control)

**Key Features:**
- Policy enforcement
- Charging rule application
- Session management
- IP allocation

### PCRF (Policy and Charging Rules Function)
The PCRF is the central policy decision point in the network.

**Applications:**
- Gx Application (Policy and Charging Control)
- Rx Application (Application Function)
- Sy Application (Spending Limit Control)

**Key Features:**
- Policy decision making
- Session binding across applications
- Cross-application coordination
- Centralized session management

### AF (Application Function)
The AF provides application-specific services and media control.

**Applications:**
- Rx Application (Application Function)

**Key Features:**
- Media resource management
- QoS control
- IMS integration
- Media session coordination

### OCS (Online Charging System)
The OCS handles real-time charging and spending limit control.

**Applications:**
- Sy Application (Spending Limit Control)

**Key Features:**
- Real-time charging
- Spending limit enforcement
- Credit management
- Charging session coordination

### DSC (Diameter Signaling Controller)
The DSC provides routing and load balancing for Diameter messages.

**Key Features:**
- Message routing
- Load balancing
- Failover management
- Network optimization

## Entity Usage Patterns

### Basic Entity Setup
```python
from diameter_telecom.entities_3gpp import PCEF, PCRF, OCS
from diameter_telecom.diameter.constants import APP_3GPP_GX, APP_3GPP_SY

# Create entities
pcef = PCEF("pcef.mobile.net", "mobile.net", ["127.0.0.1"], tcp_port=3868)
pcrf = PCRF("pcrf.mobile.net", "mobile.net", ["127.0.0.1"], tcp_port=3869)
ocs = OCS("ocs.billing.net", "billing.net", ["127.0.0.1"], tcp_port=3870)

# Setup peer relationships
pcef.add_node_as_peer(pcrf.node, app_id=APP_3GPP_GX, initiate_connection=True)
pcrf.add_node_as_peer(pcef.node, app_id=APP_3GPP_GX, initiate_connection=False)
pcrf.add_node_as_peer(ocs.node, app_id=APP_3GPP_SY, initiate_connection=True)
ocs.add_node_as_peer(pcrf.node, app_id=APP_3GPP_SY, initiate_connection=False)

# Setup applications
pcef.setup_gx_app()
pcrf.setup_gx_app()
pcrf.setup_sy_app()
ocs.setup_sy_app()

# Start entities
pcef.start()
pcrf.start()
ocs.start()
```

### Advanced Entity Configuration
```python
# Custom configuration
pcrf = PCRF(
    origin_host="pcrf.mobile.net",
    realm_name="mobile.net",
    ip_addresses=["127.0.0.1", "192.168.1.100"],
    tcp_port=3869,
    vendor_ids=[10415, 12345],  # 3GPP + custom vendor
    capabilities={
        "auth_apps": [APP_3GPP_GX, APP_3GPP_RX, APP_3GPP_SY],
        "acct_apps": [],
        "vendor_specific": [10415]
    }
)

# Custom application setup
pcrf.setup_gx_app(max_threads=5, request_handler=custom_gx_handler)
pcrf.setup_rx_app(max_threads=3, request_handler=custom_rx_handler)
pcrf.setup_sy_app(max_threads=2, request_handler=custom_sy_handler)
```

## Entity Relationships

### PCEF-PCRF Relationship
```python
# PCEF initiates connection to PCRF
pcef.add_node_as_peer(
    pcrf.node, 
    app_id=APP_3GPP_GX, 
    initiate_connection=True
)

# PCRF accepts connection from PCEF
pcrf.add_node_as_peer(
    pcef.node, 
    app_id=APP_3GPP_GX, 
    initiate_connection=False
)
```

### PCRF-OCS Relationship
```python
# PCRF initiates connection to OCS
pcrf.add_node_as_peer(
    ocs.node, 
    app_id=APP_3GPP_SY, 
    initiate_connection=True
)

# OCS accepts connection from PCRF
ocs.add_node_as_peer(
    pcrf.node, 
    app_id=APP_3GPP_SY, 
    initiate_connection=False
)
```

### PCRF-AF Relationship
```python
# PCRF initiates connection to AF
pcrf.add_node_as_peer(
    af.node, 
    app_id=APP_3GPP_RX, 
    initiate_connection=True
)

# AF accepts connection from PCRF
af.add_node_as_peer(
    pcrf.node, 
    app_id=APP_3GPP_RX, 
    initiate_connection=False
)
```

## Application Management

### Gx Application (Policy and Charging Control)
```python
# Setup Gx application on PCEF
pcef.setup_gx_app(
    max_threads=5,
    request_handler=custom_gx_handler,
    session_timeout=3600
)

# Setup Gx application on PCRF
pcrf.setup_gx_app(
    max_threads=10,
    request_handler=custom_gx_handler,
    session_timeout=3600
)
```

### Rx Application (Application Function)
```python
# Setup Rx application on PCRF
pcrf.setup_rx_app(
    max_threads=3,
    request_handler=custom_rx_handler,
    session_timeout=1800
)

# Setup Rx application on AF
af.setup_rx_app(
    max_threads=2,
    request_handler=custom_rx_handler,
    session_timeout=1800
)
```

### Sy Application (Spending Limit Control)
```python
# Setup Sy application on PCRF
pcrf.setup_sy_app(
    max_threads=2,
    request_handler=custom_sy_handler,
    session_timeout=7200
)

# Setup Sy application on OCS
ocs.setup_sy_app(
    max_threads=5,
    request_handler=custom_sy_handler,
    session_timeout=7200
)
```

## Custom Request Handlers

### Gx Request Handler
```python
def custom_gx_handler(request, answer):
    """Custom Gx request handler"""
    # Extract session information
    session_id = request.get_avp("Session-Id").data.decode()
    subscriber = identify_subscriber(request)
    
    # Apply business logic
    if request.command_code == CCR_INITIAL:
        # Handle initial request
        apply_initial_policy(subscriber, request, answer)
    elif request.command_code == CCR_UPDATE:
        # Handle update request
        apply_update_policy(subscriber, request, answer)
    elif request.command_code == CCR_TERMINATION:
        # Handle termination request
        cleanup_session(subscriber, request, answer)
    
    return answer
```

### Rx Request Handler
```python
def custom_rx_handler(request, answer):
    """Custom Rx request handler"""
    # Extract media information
    media_info = extract_media_info(request)
    subscriber = identify_subscriber(request)
    
    # Apply media policy
    if request.command_code == AAR:
        # Handle authorization request
        authorize_media_session(subscriber, media_info, request, answer)
    elif request.command_code == STR:
        # Handle session termination
        terminate_media_session(subscriber, request, answer)
    
    return answer
```

### Sy Request Handler
```python
def custom_sy_handler(request, answer):
    """Custom Sy request handler"""
    # Extract charging information
    charging_info = extract_charging_info(request)
    subscriber = identify_subscriber(request)
    
    # Apply charging policy
    if request.command_code == SLR:
        # Handle spending limit request
        check_spending_limit(subscriber, charging_info, request, answer)
    elif request.command_code == STR:
        # Handle session termination
        finalize_charging(subscriber, request, answer)
    
    return answer
```

## Entity Lifecycle

### Initialization
```python
# 1. Create entity
pcrf = PCRF("pcrf.example.com", "example.com")

# 2. Configure entity
pcrf.ip_addresses = ["127.0.0.1", "192.168.1.100"]
pcrf.tcp_port = 3869
pcrf.vendor_ids = [10415]

# 3. Setup applications
pcrf.setup_gx_app()
pcrf.setup_rx_app()
pcrf.setup_sy_app()

# 4. Add peers
pcrf.add_node_as_peer(pcef.node, app_id=APP_3GPP_GX)
pcrf.add_node_as_peer(af.node, app_id=APP_3GPP_RX)
pcrf.add_node_as_peer(ocs.node, app_id=APP_3GPP_SY)
```

### Starting Entities
```python
# Start entity
pcrf.start()

# Wait for ready
pcrf.wait_for_ready()

# Check entity status
if pcrf.is_ready():
    print("PCRF is ready")
```

### Message Sending
```python
# Send request through specific application
gx_app = pcrf.gx_app
request, answer = gx_app.send_request_custom(message, timeout=10)

# Send request through specific peer
peer = pcrf.get_peer("pcef.example.com")
request, answer = peer.send_request(message, timeout=10)
```

### Cleanup
```python
# Stop entity
pcrf.stop()

# Cleanup is automatic
```

## Best Practices

### 1. Use Services When Possible
```python
# ✅ Recommended: Use Services for most cases
data_service = DataService(pcef=pcef, ocs=ocs)
request, answer = data_service.send_request(message)

# ❌ Avoid: Direct entity management unless needed
pcef.setup_gx_app()
pcef.start()
# ... complex setup code
```

### 2. Proper Peer Management
```python
# ✅ Good: Clear peer relationships
pcef.add_node_as_peer(pcrf.node, app_id=APP_3GPP_GX, initiate_connection=True)
pcrf.add_node_as_peer(pcef.node, app_id=APP_3GPP_GX, initiate_connection=False)

# ❌ Avoid: Bidirectional initiation
pcef.add_node_as_peer(pcrf.node, app_id=APP_3GPP_GX, initiate_connection=True)
pcrf.add_node_as_peer(pcef.node, app_id=APP_3GPP_GX, initiate_connection=True)
```

### 3. Application Configuration
```python
# ✅ Good: Appropriate thread counts
pcrf.setup_gx_app(max_threads=10)  # High volume
pcrf.setup_rx_app(max_threads=3)  # Medium volume
pcrf.setup_sy_app(max_threads=2)   # Low volume

# ❌ Avoid: Over-threading
pcrf.setup_gx_app(max_threads=100)  # Unnecessary overhead
```

## Common Patterns

### Multi-Entity Network
```python
# Create all entities
pcef = PCEF("pcef.mobile.net", "mobile.net")
pcrf = PCRF("pcrf.mobile.net", "mobile.net")
af = AF("af.ims.net", "ims.net")
ocs = OCS("ocs.billing.net", "billing.net")

# Setup peer relationships
pcef.add_node_as_peer(pcrf.node, app_id=APP_3GPP_GX, initiate_connection=True)
pcrf.add_node_as_peer(pcef.node, app_id=APP_3GPP_GX, initiate_connection=False)
pcrf.add_node_as_peer(af.node, app_id=APP_3GPP_RX, initiate_connection=True)
af.add_node_as_peer(pcrf.node, app_id=APP_3GPP_RX, initiate_connection=False)
pcrf.add_node_as_peer(ocs.node, app_id=APP_3GPP_SY, initiate_connection=True)
ocs.add_node_as_peer(pcrf.node, app_id=APP_3GPP_SY, initiate_connection=False)

# Setup applications
pcef.setup_gx_app()
pcrf.setup_gx_app()
pcrf.setup_rx_app()
af.setup_rx_app()
pcrf.setup_sy_app()
ocs.setup_sy_app()

# Start all entities
pcef.start()
pcrf.start()
af.start()
ocs.start()
```

### Entity Monitoring
```python
# Monitor entity status
def monitor_entities():
    entities = [pcef, pcrf, af, ocs]
    for entity in entities:
        if entity.is_ready():
            print(f"{entity.origin_host} is ready")
        else:
            print(f"{entity.origin_host} is not ready")

# Monitor peer connections
def monitor_peers():
    for entity in [pcef, pcrf, af, ocs]:
        for peer in entity.node.peers:
            if peer.is_connected():
                print(f"{entity.origin_host} -> {peer.origin_host}: Connected")
            else:
                print(f"{entity.origin_host} -> {peer.origin_host}: Disconnected")
```

## Next Steps

1. **Try Examples**: Check out the [entity examples](../examples/pcef_pcrf_connection.md) to see entities in action
2. **Session Management**: Understand [Session Management](sessions.md) for advanced scenarios
3. **Message Processing**: Dive into [Message Processing](message_processing.md) for custom logic
4. **API Reference**: Explore the [API documentation](../api/entities/pcrf.md) for detailed class information
