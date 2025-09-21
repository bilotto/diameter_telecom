# Multi-Service Advanced Example

This advanced example demonstrates concurrent DataService and VoiceService operations in a complex multi-service network with multiple carriers and realistic subscriber bases.

## Overview

The Multi-Service Advanced example showcases:

- **Concurrent Services**: DataService and VoiceService operating simultaneously
- **Multiple Carriers**: European, American, and Asian carriers with realistic subscriber bases
- **Performance Simulation**: 45+ subscribers with concurrent sessions
- **Network-Wide Statistics**: Comprehensive performance monitoring and analysis
- **Real-World Scenarios**: Production-like telecom network simulation

## Architecture

```
📊 Multi-Service Layer
├─ DataService (PCEF + OCS coordination)
├─ VoiceService (PCEF + AF coordination)
├─ SessionManager (Centralized session management)
└─ MessageProcessingPipeline (Stage-based processing)

🔧 Network Entities
├─ PCEF (Policy and Charging Enforcement)
├─ PCRF (Policy and Charging Rules)
├─ AF (Application Function - IMS)
└─ OCS (Online Charging System)

⚙️ Base Layer
└─ Core Diameter protocol implementation
```

## Key Features Demonstrated

### 1. Multi-Service Network Setup
```python
# Create network entities
pcef = PCEF("pcef.mobile.net", "mobile.net", ["127.0.0.1"], tcp_port=3868)
pcrf = PCRF("pcrf.mobile.net", "mobile.net", ["127.0.0.1"], tcp_port=3869)
af = AF("af.ims.net", "ims.net", ["127.0.0.1"], tcp_port=3871)
ocs = OCS("ocs.billing.net", "billing.net", ["127.0.0.1"], tcp_port=3870)

# Establish peer relationships
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

# Start entities
pcef.start()
pcrf.start()
af.start()
ocs.start()
```

### 2. Service Configuration
```python
# Create services
data_service = DataService(pcef=pcef, ocs=ocs)
voice_service = VoiceService(pcef=pcef, af=af)

# Configure shared session manager
session_manager = SessionManager()
data_service.set_session_manager(session_manager)
voice_service.set_session_manager(session_manager)

# Configure multi-carrier support
carriers = {
    "european": Carrier("European Mobile", "EU", {...}),
    "american": Carrier("American Wireless", "US", {...}),
    "asian": Carrier("Asian Telecom", "AS", {...})
}

data_service.configure_multi_carrier(carriers)
voice_service.configure_ims({
    "p_cscf_address": "p-cscf.ims.net",
    "s_cscf_address": "s-cscf.ims.net",
    "media_gateway": "mgw.ims.net"
})
```

### 3. Subscriber Base Creation
```python
def create_realistic_subscriber_base():
    """Create realistic subscriber base with different profiles"""
    
    subscribers = []
    
    # European subscribers
    for i in range(15):
        subscriber = Subscriber(
            msisdn=f"3312345678{i:02d}",
            imsi=f"2081234567890{i:02d}",
            carrier=carriers["european"],
            plan=random.choice(["standard", "premium", "business"]),
            apn=random.choice(["internet", "premium", "iot"])
        )
        subscribers.append(subscriber)
    
    # American subscribers
    for i in range(15):
        subscriber = Subscriber(
            msisdn=f"1555123456{i:02d}",
            imsi=f"3101234567890{i:02d}",
            carrier=carriers["american"],
            plan=random.choice(["basic", "premium", "unlimited"]),
            apn=random.choice(["internet", "premium"])
        )
        subscribers.append(subscriber)
    
    # Asian subscribers
    for i in range(15):
        subscriber = Subscriber(
            msisdn=f"8613800000{i:02d}",
            imsi=f"4601234567890{i:02d}",
            carrier=carriers["asian"],
            plan=random.choice(["standard", "premium", "iot"]),
            apn=random.choice(["internet", "iot"])
        )
        subscribers.append(subscriber)
    
    return subscribers
```

## Concurrent Service Operations

### Data Service Operations
```python
def run_data_service_operations(subscribers, duration=300):
    """Run concurrent data service operations"""
    
    start_time = time.time()
    active_sessions = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        # Start data sessions for all subscribers
        futures = []
        for subscriber in subscribers:
            future = executor.submit(create_data_session, subscriber)
            futures.append((subscriber, future))
        
        # Wait for initial sessions
        for subscriber, future in futures:
            try:
                result = future.result(timeout=30)
                if result:
                    active_sessions[subscriber.msisdn] = subscriber
                    print(f"Data session started for {subscriber.msisdn}")
            except Exception as e:
                print(f"Failed to start data session for {subscriber.msisdn}: {e}")
        
        # Simulate session updates
        while time.time() - start_time < duration:
            # Randomly update sessions
            for subscriber in list(active_sessions.values()):
                if random.random() < 0.1:  # 10% chance per iteration
                    try:
                        update_data_session(subscriber)
                        print(f"Data session updated for {subscriber.msisdn}")
                    except Exception as e:
                        print(f"Failed to update data session for {subscriber.msisdn}: {e}")
            
            time.sleep(5)  # Wait 5 seconds between iterations
        
        # Terminate all sessions
        for subscriber in active_sessions.values():
            try:
                terminate_data_session(subscriber)
                print(f"Data session terminated for {subscriber.msisdn}")
            except Exception as e:
                print(f"Failed to terminate data session for {subscriber.msisdn}: {e}")
```

### Voice Service Operations
```python
def run_voice_service_operations(subscribers, duration=300):
    """Run concurrent voice service operations"""
    
    start_time = time.time()
    active_calls = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Start voice calls for subscribers
        futures = []
        for i in range(0, len(subscribers), 2):
            if i + 1 < len(subscribers):
                calling_subscriber = subscribers[i]
                called_subscriber = subscribers[i + 1]
                
                future = executor.submit(create_voice_call, calling_subscriber, called_subscriber)
                futures.append((calling_subscriber, called_subscriber, future))
        
        # Wait for calls to complete
        for calling_subscriber, called_subscriber, future in futures:
            try:
                result = future.result(timeout=60)
                if result:
                    call_id = f"{calling_subscriber.msisdn}-{called_subscriber.msisdn}"
                    active_calls[call_id] = {
                        "calling": calling_subscriber,
                        "called": called_subscriber,
                        "start_time": time.time()
                    }
                    print(f"Voice call started: {call_id}")
            except Exception as e:
                print(f"Failed to start voice call: {calling_subscriber.msisdn} -> {called_subscriber.msisdn}: {e}")
        
        # Simulate call modifications
        while time.time() - start_time < duration:
            # Randomly modify calls
            for call_id in list(active_calls.keys()):
                if random.random() < 0.05:  # 5% chance per iteration
                    try:
                        call_info = active_calls[call_id]
                        modify_voice_call(call_info["calling"], call_info["called"])
                        print(f"Voice call modified: {call_id}")
                    except Exception as e:
                        print(f"Failed to modify voice call: {call_id}: {e}")
            
            time.sleep(10)  # Wait 10 seconds between iterations
        
        # Terminate all calls
        for call_id, call_info in active_calls.items():
            try:
                terminate_voice_call(call_info["calling"], call_info["called"])
                print(f"Voice call terminated: {call_id}")
            except Exception as e:
                print(f"Failed to terminate voice call: {call_id}: {e}")
```

## Network-Wide Statistics

### Performance Monitoring
```python
def monitor_network_performance(session_manager, duration=300):
    """Monitor network-wide performance metrics"""
    
    start_time = time.time()
    metrics_history = []
    
    while time.time() - start_time < duration:
        # Get current statistics
        stats = session_manager.get_network_statistics()
        
        # Calculate performance metrics
        performance_metrics = {
            "timestamp": time.time(),
            "total_sessions": stats.get("total_sessions", 0),
            "active_sessions": stats.get("active_sessions", 0),
            "terminated_sessions": stats.get("terminated_sessions", 0),
            "messages_processed": stats.get("messages_processed", 0),
            "errors": stats.get("errors", 0),
            "avg_response_time": stats.get("avg_response_time", 0),
            "memory_usage": stats.get("memory_usage", 0),
            "cpu_usage": stats.get("cpu_usage", 0)
        }
        
        # Store metrics
        metrics_history.append(performance_metrics)
        
        # Print current metrics
        print(f"Network Performance Metrics:")
        print(f"  Total Sessions: {performance_metrics['total_sessions']}")
        print(f"  Active Sessions: {performance_metrics['active_sessions']}")
        print(f"  Messages Processed: {performance_metrics['messages_processed']}")
        print(f"  Errors: {performance_metrics['errors']}")
        print(f"  Avg Response Time: {performance_metrics['avg_response_time']:.2f}ms")
        print(f"  Memory Usage: {performance_metrics['memory_usage']:.2f}MB")
        
        time.sleep(30)  # Update every 30 seconds
    
    return metrics_history
```

### Service-Specific Statistics
```python
def get_service_statistics(data_service, voice_service):
    """Get service-specific statistics"""
    
    # Data service statistics
    data_stats = data_service.get_statistics()
    print(f"Data Service Statistics:")
    print(f"  Gx Requests: {data_stats.get('gx_requests', 0)}")
    print(f"  Sy Requests: {data_stats.get('sy_requests', 0)}")
    print(f"  Data Sessions: {data_stats.get('data_sessions', 0)}")
    print(f"  Charging Sessions: {data_stats.get('charging_sessions', 0)}")
    
    # Voice service statistics
    voice_stats = voice_service.get_statistics()
    print(f"Voice Service Statistics:")
    print(f"  Gx Requests: {voice_stats.get('gx_requests', 0)}")
    print(f"  Rx Requests: {voice_stats.get('rx_requests', 0)}")
    print(f"  Voice Calls: {voice_stats.get('voice_calls', 0)}")
    print(f"  Video Calls: {voice_stats.get('video_calls', 0)}")
    
    return data_stats, voice_stats
```

### Carrier-Specific Analysis
```python
def analyze_carrier_performance(session_manager, carriers):
    """Analyze performance by carrier"""
    
    carrier_stats = {}
    
    for carrier_name, carrier in carriers.items():
        # Get carrier-specific statistics
        stats = session_manager.get_carrier_statistics(carrier_name)
        
        carrier_stats[carrier_name] = {
            "subscribers": stats.get("subscribers", 0),
            "sessions": stats.get("sessions", 0),
            "messages": stats.get("messages", 0),
            "errors": stats.get("errors", 0),
            "avg_response_time": stats.get("avg_response_time", 0)
        }
        
        print(f"{carrier_name} Carrier Statistics:")
        print(f"  Subscribers: {carrier_stats[carrier_name]['subscribers']}")
        print(f"  Sessions: {carrier_stats[carrier_name]['sessions']}")
        print(f"  Messages: {carrier_stats[carrier_name]['messages']}")
        print(f"  Errors: {carrier_stats[carrier_name]['errors']}")
        print(f"  Avg Response Time: {carrier_stats[carrier_name]['avg_response_time']:.2f}ms")
    
    return carrier_stats
```

## Advanced Scenarios

### Mixed Service Operations
```python
def run_mixed_service_operations(subscribers, duration=300):
    """Run mixed data and voice service operations"""
    
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        # Submit mixed operations
        futures = []
        
        # Data service operations
        for subscriber in subscribers:
            future = executor.submit(create_data_session, subscriber)
            futures.append(("data", subscriber, future))
        
        # Voice service operations
        for i in range(0, len(subscribers), 2):
            if i + 1 < len(subscribers):
                calling_subscriber = subscribers[i]
                called_subscriber = subscribers[i + 1]
                
                future = executor.submit(create_voice_call, calling_subscriber, called_subscriber)
                futures.append(("voice", f"{calling_subscriber.msisdn}-{called_subscriber.msisdn}", future))
        
        # Wait for all operations to complete
        for operation_type, identifier, future in futures:
            try:
                result = future.result(timeout=60)
                if result:
                    print(f"{operation_type} operation completed: {identifier}")
                else:
                    print(f"{operation_type} operation failed: {identifier}")
            except Exception as e:
                print(f"{operation_type} operation error: {identifier}: {e}")
```

### Load Testing
```python
def run_load_test(subscribers, duration=600):
    """Run load test with high concurrent operations"""
    
    start_time = time.time()
    operation_count = 0
    success_count = 0
    error_count = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        while time.time() - start_time < duration:
            # Submit random operations
            futures = []
            
            for _ in range(10):  # 10 operations per batch
                operation_type = random.choice(["data", "voice"])
                
                if operation_type == "data":
                    subscriber = random.choice(subscribers)
                    future = executor.submit(create_data_session, subscriber)
                    futures.append(("data", subscriber.msisdn, future))
                else:
                    if len(subscribers) >= 2:
                        calling_subscriber = random.choice(subscribers)
                        called_subscriber = random.choice([s for s in subscribers if s != calling_subscriber])
                        future = executor.submit(create_voice_call, calling_subscriber, called_subscriber)
                        futures.append(("voice", f"{calling_subscriber.msisdn}-{called_subscriber.msisdn}", future))
            
            # Wait for batch completion
            for operation_type, identifier, future in futures:
                try:
                    result = future.result(timeout=30)
                    operation_count += 1
                    if result:
                        success_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    operation_count += 1
                    error_count += 1
                    print(f"Load test error: {operation_type} {identifier}: {e}")
            
            # Brief pause between batches
            time.sleep(1)
    
    # Calculate performance metrics
    success_rate = (success_count / operation_count) * 100 if operation_count > 0 else 0
    error_rate = (error_count / operation_count) * 100 if operation_count > 0 else 0
    operations_per_second = operation_count / duration
    
    print(f"Load Test Results:")
    print(f"  Total Operations: {operation_count}")
    print(f"  Successful Operations: {success_count}")
    print(f"  Failed Operations: {error_count}")
    print(f"  Success Rate: {success_rate:.2f}%")
    print(f"  Error Rate: {error_rate:.2f}%")
    print(f"  Operations/Second: {operations_per_second:.2f}")
    
    return {
        "total_operations": operation_count,
        "successful_operations": success_count,
        "failed_operations": error_count,
        "success_rate": success_rate,
        "error_rate": error_rate,
        "operations_per_second": operations_per_second
    }
```

## Running the Example

### Basic Usage
```bash
# Run the multi-service advanced example
python examples/multi_service_advanced.py
```

### Custom Configuration
```python
# Customize the example
def run_custom_multi_service_example():
    # Create custom network
    custom_network = MultiServiceNetwork(
        carriers={
            "custom1": Carrier("Custom Carrier 1", "US", {...}),
            "custom2": Carrier("Custom Carrier 2", "EU", {...})
        },
        services=["data", "voice"],
        max_concurrent_operations=100
    )
    
    # Create custom subscribers
    subscribers = create_custom_subscriber_base(custom_network)
    
    # Run mixed operations
    run_mixed_service_operations(subscribers, duration=600)
```

### Performance Testing
```python
# Run performance test
def run_multi_service_performance_test():
    # Create large subscriber base
    subscribers = create_realistic_subscriber_base()
    
    # Run load test
    load_test_results = run_load_test(subscribers, duration=600)
    
    # Print performance results
    print(f"Multi-Service Performance Results:")
    print(f"  Total Operations: {load_test_results['total_operations']}")
    print(f"  Success Rate: {load_test_results['success_rate']:.2f}%")
    print(f"  Operations/Second: {load_test_results['operations_per_second']:.2f}")
```

## Expected Output

The example will demonstrate:

1. **Multi-Service Network**: DataService and VoiceService operating concurrently
2. **Realistic Subscriber Base**: 45+ subscribers across multiple carriers
3. **Concurrent Operations**: Simultaneous data and voice operations
4. **Performance Monitoring**: Real-time network-wide statistics
5. **Load Testing**: High-concurrency performance testing
6. **Carrier Analysis**: Performance analysis by carrier
7. **Service Coordination**: Seamless coordination between services

## Key Learning Points

1. **Multi-Service Architecture**: How multiple services work together
2. **Concurrent Operations**: Managing concurrent data and voice operations
3. **Performance Monitoring**: Network-wide performance analysis
4. **Load Testing**: High-concurrency performance testing
5. **Real-World Scenarios**: Production-like telecom network simulation
6. **Service Coordination**: Seamless coordination between different services

## Next Steps

1. **Try the Example**: Run the multi-service advanced example
2. **Modify Scenarios**: Customize carriers, subscribers, and operations
3. **Performance Tuning**: Experiment with different performance parameters
4. **Explore Other Examples**: Check out [Data Service Comprehensive](data_service_comprehensive.md) and [Voice Service Comprehensive](voice_service_comprehensive.md)
5. **API Reference**: Explore the [API documentation](../api/services/data.md) for detailed class information
