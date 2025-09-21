# Data Service Comprehensive Example

This comprehensive example demonstrates the complete DataService usage with multiple carriers, different subscriber scenarios, and full session lifecycle management.

## Overview

The Data Service Comprehensive example showcases:

- **Multiple Carriers**: European, American, and Asian carriers with different APNs
- **5 Subscriber Scenarios**: Regular, premium, IoT, heavy usage, and roaming subscribers
- **Full Session Lifecycle**: Initial → Updates → Termination flows
- **PCEF-PCRF-OCS Integration**: Complete Gx/Sy coordination
- **Performance Simulation**: 45+ subscribers with concurrent sessions

## Architecture

```
📊 Data Service Layer
├─ DataService (PCEF + OCS coordination)
├─ SessionManager (Centralized session management)
└─ MessageProcessingPipeline (Stage-based processing)

🔧 Network Entities
├─ PCEF (Policy and Charging Enforcement)
├─ PCRF (Policy and Charging Rules)
└─ OCS (Online Charging System)

⚙️ Base Layer
└─ Core Diameter protocol implementation
```

## Key Features Demonstrated

### 1. Multi-Carrier Network
```python
# European carrier with premium services
european_carrier = Carrier(
    name="European Mobile",
    country="EU",
    apns={
        "internet": APN("internet.eu.mobile", "internet", "10.0.1.0/24"),
        "premium": APN("premium.eu.mobile", "premium", "10.0.2.0/24"),
        "iot": APN("iot.eu.mobile", "iot", "10.0.3.0/24")
    }
)

# American carrier with high-speed data
american_carrier = Carrier(
    name="American Wireless",
    country="US",
    apns={
        "internet": APN("internet.us.wireless", "internet", "10.1.1.0/24"),
        "premium": APN("premium.us.wireless", "premium", "10.1.2.0/24")
    }
)

# Asian carrier with IoT focus
asian_carrier = Carrier(
    name="Asian Telecom",
    country="AS",
    apns={
        "internet": APN("internet.as.telecom", "internet", "10.2.1.0/24"),
        "iot": APN("iot.as.telecom", "iot", "10.2.2.0/24")
    }
)
```

### 2. Subscriber Scenarios
```python
# Regular subscriber with standard data plan
regular_subscriber = Subscriber(
    msisdn="1234567890",
    imsi="123456789012345",
    carrier=european_carrier,
    plan="standard",
    apn="internet"
)

# Premium subscriber with high-speed data
premium_subscriber = Subscriber(
    msisdn="2345678901",
    imsi="234567890123456",
    carrier=american_carrier,
    plan="premium",
    apn="premium"
)

# IoT subscriber with specialized plan
iot_subscriber = Subscriber(
    msisdn="3456789012",
    imsi="345678901234567",
    carrier=asian_carrier,
    plan="iot",
    apn="iot"
)

# Heavy usage subscriber with monitoring
heavy_usage_subscriber = Subscriber(
    msisdn="4567890123",
    imsi="456789012345678",
    carrier=european_carrier,
    plan="heavy_usage",
    apn="internet"
)

# Roaming subscriber with international access
roaming_subscriber = Subscriber(
    msisdn="5678901234",
    imsi="567890123456789",
    carrier=american_carrier,
    plan="roaming",
    apn="internet",
    roaming=True
)
```

### 3. Network Entity Setup
```python
# Create network entities
pcef = PCEF("pcef.mobile.net", "mobile.net", ["127.0.0.1"], tcp_port=3868)
pcrf = PCRF("pcrf.mobile.net", "mobile.net", ["127.0.0.1"], tcp_port=3869)
ocs = OCS("ocs.billing.net", "billing.net", ["127.0.0.1"], tcp_port=3870)

# Establish peer relationships
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

### 4. DataService Configuration
```python
# Create DataService
data_service = DataService(pcef=pcef, ocs=ocs)
data_service.set_session_manager(SessionManager())

# Configure service for multi-carrier support
data_service.configure_multi_carrier({
    "european": european_carrier,
    "american": american_carrier,
    "asian": asian_carrier
})
```

## Session Lifecycle Management

### Initial Session Creation
```python
def create_initial_session(subscriber):
    """Create initial Gx session for subscriber"""
    # Create CCR Initial message
    ccr_message = create_ccr_initial_message(
        subscriber=subscriber,
        session_id=f"gx-{subscriber.msisdn}-{int(time.time())}",
        apn=subscriber.apn,
        ip_address=subscriber.carrier.get_ip_address()
    )
    
    # Send request through DataService
    request, answer = data_service.send_request(ccr_message)
    
    if answer.result_code == DIAMETER_SUCCESS:
        # Session created successfully
        gx_session = data_service.get_gx_session(subscriber)
        print(f"Gx session created: {gx_session.session_id}")
        
        # Create Sy session for charging
        create_charging_session(subscriber, gx_session)
    
    return request, answer
```

### Session Updates
```python
def update_session(subscriber, update_type="usage"):
    """Update existing session"""
    gx_session = data_service.get_gx_session(subscriber)
    
    if not gx_session:
        print(f"No active session for subscriber {subscriber.msisdn}")
        return None
    
    # Create CCR Update message
    ccr_update = create_ccr_update_message(
        subscriber=subscriber,
        session_id=gx_session.session_id,
        update_type=update_type
    )
    
    # Send update request
    request, answer = data_service.send_request(ccr_update)
    
    if answer.result_code == DIAMETER_SUCCESS:
        print(f"Session updated: {gx_session.session_id}")
        
        # Update charging session if needed
        update_charging_session(subscriber, gx_session)
    
    return request, answer
```

### Session Termination
```python
def terminate_session(subscriber):
    """Terminate subscriber session"""
    gx_session = data_service.get_gx_session(subscriber)
    
    if not gx_session:
        print(f"No active session for subscriber {subscriber.msisdn}")
        return None
    
    # Create CCR Termination message
    ccr_termination = create_ccr_termination_message(
        subscriber=subscriber,
        session_id=gx_session.session_id
    )
    
    # Send termination request
    request, answer = data_service.send_request(ccr_termination)
    
    if answer.result_code == DIAMETER_SUCCESS:
        print(f"Session terminated: {gx_session.session_id}")
        
        # Terminate charging session
        terminate_charging_session(subscriber, gx_session)
    
    return request, answer
```

## Charging Integration

### Sy Session Management
```python
def create_charging_session(subscriber, gx_session):
    """Create Sy session for charging"""
    # Create SLR Initial message
    slr_message = create_slr_initial_message(
        subscriber=subscriber,
        session_id=f"sy-{subscriber.msisdn}-{int(time.time())}",
        gx_session_id=gx_session.session_id
    )
    
    # Send request through DataService
    request, answer = data_service.send_request(slr_message)
    
    if answer.result_code == DIAMETER_SUCCESS:
        sy_session = data_service.get_sy_session(subscriber)
        print(f"Sy session created: {sy_session.session_id}")
        print(f"Bound to Gx session: {sy_session.gx_session_id}")
    
    return request, answer

def update_charging_session(subscriber, gx_session):
    """Update charging session"""
    sy_session = data_service.get_sy_session(subscriber)
    
    if not sy_session:
        return None
    
    # Create SLR Update message
    slr_update = create_slr_update_message(
        subscriber=subscriber,
        session_id=sy_session.session_id,
        gx_session_id=gx_session.session_id
    )
    
    # Send update request
    request, answer = data_service.send_request(slr_update)
    
    if answer.result_code == DIAMETER_SUCCESS:
        print(f"Charging session updated: {sy_session.session_id}")
    
    return request, answer
```

## Performance Simulation

### Concurrent Session Management
```python
import concurrent.futures
import time

def simulate_concurrent_sessions(subscribers, duration=300):
    """Simulate concurrent sessions for multiple subscribers"""
    start_time = time.time()
    active_sessions = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Start initial sessions for all subscribers
        futures = []
        for subscriber in subscribers:
            future = executor.submit(create_initial_session, subscriber)
            futures.append((subscriber, future))
        
        # Wait for initial sessions
        for subscriber, future in futures:
            try:
                request, answer = future.result(timeout=30)
                if answer.result_code == DIAMETER_SUCCESS:
                    active_sessions[subscriber.msisdn] = subscriber
                    print(f"Session started for {subscriber.msisdn}")
            except Exception as e:
                print(f"Failed to start session for {subscriber.msisdn}: {e}")
        
        # Simulate session updates
        while time.time() - start_time < duration:
            # Randomly update sessions
            for subscriber in list(active_sessions.values()):
                if random.random() < 0.1:  # 10% chance per iteration
                    try:
                        update_session(subscriber, "usage")
                        print(f"Session updated for {subscriber.msisdn}")
                    except Exception as e:
                        print(f"Failed to update session for {subscriber.msisdn}: {e}")
            
            time.sleep(5)  # Wait 5 seconds between iterations
        
        # Terminate all sessions
        for subscriber in active_sessions.values():
            try:
                terminate_session(subscriber)
                print(f"Session terminated for {subscriber.msisdn}")
            except Exception as e:
                print(f"Failed to terminate session for {subscriber.msisdn}: {e}")
```

### Performance Monitoring
```python
def monitor_performance(session_manager, duration=300):
    """Monitor performance metrics during simulation"""
    start_time = time.time()
    metrics = {
        "messages_processed": 0,
        "sessions_created": 0,
        "sessions_updated": 0,
        "sessions_terminated": 0,
        "errors": 0
    }
    
    while time.time() - start_time < duration:
        # Get current statistics
        stats = session_manager.get_session_statistics()
        
        # Update metrics
        metrics["messages_processed"] = stats.get("messages_processed", 0)
        metrics["sessions_created"] = stats.get("sessions_created", 0)
        metrics["sessions_updated"] = stats.get("sessions_updated", 0)
        metrics["sessions_terminated"] = stats.get("sessions_terminated", 0)
        metrics["errors"] = stats.get("errors", 0)
        
        # Print metrics
        print(f"Performance Metrics:")
        print(f"  Messages Processed: {metrics['messages_processed']}")
        print(f"  Sessions Created: {metrics['sessions_created']}")
        print(f"  Sessions Updated: {metrics['sessions_updated']}")
        print(f"  Sessions Terminated: {metrics['sessions_terminated']}")
        print(f"  Errors: {metrics['errors']}")
        
        time.sleep(30)  # Update every 30 seconds
    
    return metrics
```

## Running the Example

### Basic Usage
```bash
# Run the comprehensive example
python examples/data_service_comprehensive.py
```

### Custom Configuration
```python
# Customize the example
def run_custom_example():
    # Create custom carriers
    custom_carriers = [
        Carrier("Custom Carrier 1", "US", {...}),
        Carrier("Custom Carrier 2", "EU", {...})
    ]
    
    # Create custom subscribers
    custom_subscribers = [
        Subscriber("1111111111", "111111111111111", custom_carriers[0]),
        Subscriber("2222222222", "222222222222222", custom_carriers[1])
    ]
    
    # Run simulation
    simulate_concurrent_sessions(custom_subscribers, duration=600)
```

### Performance Testing
```python
# Run performance test
def run_performance_test():
    # Create large number of subscribers
    subscribers = []
    for i in range(100):
        subscriber = Subscriber(
            msisdn=f"100000000{i:02d}",
            imsi=f"10000000000000{i:02d}",
            carrier=european_carrier
        )
        subscribers.append(subscriber)
    
    # Run performance simulation
    metrics = simulate_concurrent_sessions(subscribers, duration=600)
    
    # Print performance results
    print(f"Performance Results:")
    print(f"  Total Messages: {metrics['messages_processed']}")
    print(f"  Sessions Created: {metrics['sessions_created']}")
    print(f"  Average Response Time: {metrics['avg_response_time']}ms")
    print(f"  Error Rate: {metrics['error_rate']:.2f}%")
```

## Expected Output

The example will demonstrate:

1. **Network Setup**: PCEF, PCRF, and OCS entities starting up
2. **Peer Connections**: Successful peer establishment
3. **Session Creation**: Gx and Sy sessions being created
4. **Session Updates**: Regular session updates and modifications
5. **Session Termination**: Clean session termination
6. **Performance Metrics**: Real-time performance monitoring
7. **Error Handling**: Graceful error handling and recovery

## Key Learning Points

1. **Services Architecture**: How DataService simplifies complex network operations
2. **Session Management**: Cross-application session binding and lifecycle
3. **Multi-Carrier Support**: Handling different carriers and APNs
4. **Performance Optimization**: Concurrent processing and memory management
5. **Error Resilience**: Graceful error handling and recovery
6. **Real-World Scenarios**: Practical telecom network simulation

## Next Steps

1. **Try the Example**: Run the comprehensive example to see it in action
2. **Modify Scenarios**: Customize carriers, subscribers, and session flows
3. **Performance Tuning**: Experiment with different performance parameters
4. **Explore Other Examples**: Check out [Voice Service Comprehensive](voice_service_comprehensive.md) and [Multi-Service Advanced](multi_service_advanced.md)
5. **API Reference**: Explore the [DataService API](../api/services/data.md) for detailed documentation
