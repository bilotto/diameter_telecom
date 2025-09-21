# Voice Service Comprehensive Example

This comprehensive example demonstrates the complete VoiceService usage with IMS network simulation, voice call scenarios, and Gx-Rx session coordination.

## Overview

The Voice Service Comprehensive example showcases:

- **IMS Network Simulation**: PCEF-PCRF-AF entities with media control
- **Voice Call Scenarios**: Voice, video, HD video, and conference calls
- **Gx-Rx Session Binding**: Policy and media session coordination
- **Real-World IMS Flows**: Complete IMS call flows and modifications
- **Media Resource Management**: QoS control and media session handling

## Architecture

```
📊 Voice Service Layer
├─ VoiceService (PCEF + AF coordination)
├─ SessionManager (Centralized session management)
└─ MessageProcessingPipeline (Stage-based processing)

🔧 Network Entities
├─ PCEF (Policy and Charging Enforcement)
├─ PCRF (Policy and Charging Rules)
└─ AF (Application Function - IMS)

⚙️ Base Layer
└─ Core Diameter protocol implementation
```

## Key Features Demonstrated

### 1. IMS Network Setup
```python
# IMS network entities
pcef = PCEF("pcef.ims.net", "ims.net", ["127.0.0.1"], tcp_port=3868)
pcrf = PCRF("pcrf.ims.net", "ims.net", ["127.0.0.1"], tcp_port=3869)
af = AF("af.ims.net", "ims.net", ["127.0.0.1"], tcp_port=3871)

# Establish peer relationships
pcef.add_node_as_peer(pcrf.node, app_id=APP_3GPP_GX, initiate_connection=True)
pcrf.add_node_as_peer(pcef.node, app_id=APP_3GPP_GX, initiate_connection=False)
pcrf.add_node_as_peer(af.node, app_id=APP_3GPP_RX, initiate_connection=True)
af.add_node_as_peer(pcrf.node, app_id=APP_3GPP_RX, initiate_connection=False)

# Setup applications
pcef.setup_gx_app()
pcrf.setup_gx_app()
pcrf.setup_rx_app()
af.setup_rx_app()

# Start entities
pcef.start()
pcrf.start()
af.start()
```

### 2. VoiceService Configuration
```python
# Create VoiceService
voice_service = VoiceService(pcef=pcef, af=af)
voice_service.set_session_manager(SessionManager())

# Configure IMS-specific settings
voice_service.configure_ims({
    "p_cscf_address": "p-cscf.ims.net",
    "s_cscf_address": "s-cscf.ims.net",
    "media_gateway": "mgw.ims.net",
    "codec_support": ["AMR", "AMR-WB", "G.711", "G.722", "H.264"]
})
```

### 3. Voice Call Scenarios
```python
# Voice call scenario
def simulate_voice_call(calling_subscriber, called_subscriber):
    """Simulate a voice call between two subscribers"""
    
    # 1. Policy reservation (Gx)
    gx_request, gx_answer = voice_service.send_request(
        create_ccr_initial_message(calling_subscriber)
    )
    
    if gx_answer.result_code == DIAMETER_SUCCESS:
        # 2. Media reservation (Rx)
        rx_request, rx_answer = voice_service.send_request(
            create_aar_message(calling_subscriber, called_subscriber)
        )
        
        if rx_answer.result_code == DIAMETER_SUCCESS:
            # 3. Call establishment
            establish_call(calling_subscriber, called_subscriber)
            
            # 4. Call modification (e.g., add video)
            modify_call(calling_subscriber, called_subscriber, "video")
            
            # 5. Call termination
            terminate_call(calling_subscriber, called_subscriber)
    
    return gx_request, gx_answer, rx_request, rx_answer

# Video call scenario
def simulate_video_call(calling_subscriber, called_subscriber):
    """Simulate a video call between two subscribers"""
    
    # 1. Policy reservation with video support
    gx_request, gx_answer = voice_service.send_request(
        create_ccr_initial_message(calling_subscriber, media_type="video")
    )
    
    if gx_answer.result_code == DIAMETER_SUCCESS:
        # 2. Media reservation for video
        rx_request, rx_answer = voice_service.send_request(
            create_aar_message(calling_subscriber, called_subscriber, media_type="video")
        )
        
        if rx_answer.result_code == DIAMETER_SUCCESS:
            # 3. Video call establishment
            establish_video_call(calling_subscriber, called_subscriber)
            
            # 4. Quality adjustments
            adjust_video_quality(calling_subscriber, called_subscriber, "HD")
            
            # 5. Call termination
            terminate_call(calling_subscriber, called_subscriber)
    
    return gx_request, gx_answer, rx_request, rx_answer
```

## Session Coordination

### Gx-Rx Session Binding
```python
def coordinate_gx_rx_sessions(subscriber):
    """Coordinate Gx and Rx sessions for IMS calls"""
    
    # Get Gx session (policy)
    gx_session = voice_service.get_gx_session(subscriber)
    
    if not gx_session:
        print(f"No active Gx session for subscriber {subscriber.msisdn}")
        return None
    
    # Create Rx session (media)
    rx_session = voice_service.get_rx_session(subscriber)
    
    if not rx_session:
        # Create new Rx session
        rx_session = RxSession(
            session_id=f"rx-{subscriber.msisdn}-{int(time.time())}",
            subscriber=subscriber,
            af_address="af.ims.net",
            pcrf_address="pcrf.ims.net"
        )
        
        # Bind to Gx session
        rx_session.bind_to_gx_session(gx_session)
        print(f"Rx session created and bound to Gx session: {gx_session.session_id}")
    
    return rx_session

def verify_session_binding(subscriber):
    """Verify Gx-Rx session binding"""
    gx_session = voice_service.get_gx_session(subscriber)
    rx_session = voice_service.get_rx_session(subscriber)
    
    if gx_session and rx_session:
        if rx_session.gx_session_id == gx_session.session_id:
            print(f"Sessions properly bound: Gx={gx_session.session_id}, Rx={rx_session.session_id}")
            return True
        else:
            print(f"Sessions not properly bound: Gx={gx_session.session_id}, Rx={rx_session.session_id}")
            return False
    
    return False
```

### Media Resource Management
```python
def manage_media_resources(subscriber, media_type="voice"):
    """Manage media resources for IMS calls"""
    
    # Get Rx session
    rx_session = voice_service.get_rx_session(subscriber)
    
    if not rx_session:
        print(f"No active Rx session for subscriber {subscriber.msisdn}")
        return None
    
    # Configure media resources based on call type
    if media_type == "voice":
        media_config = {
            "codec": "AMR-WB",
            "bandwidth": "64kbps",
            "quality": "HD"
        }
    elif media_type == "video":
        media_config = {
            "codec": "H.264",
            "bandwidth": "1Mbps",
            "quality": "HD",
            "resolution": "720p"
        }
    elif media_type == "conference":
        media_config = {
            "codec": "H.264",
            "bandwidth": "2Mbps",
            "quality": "HD",
            "resolution": "1080p",
            "participants": 5
        }
    
    # Update Rx session with media configuration
    rx_session.update_media_config(media_config)
    
    # Send media resource request
    aar_message = create_aar_message(subscriber, media_config=media_config)
    request, answer = voice_service.send_request(aar_message)
    
    if answer.result_code == DIAMETER_SUCCESS:
        print(f"Media resources allocated for {media_type} call")
        return True
    else:
        print(f"Failed to allocate media resources for {media_type} call")
        return False
```

## IMS Call Flows

### Basic Voice Call Flow
```python
def basic_voice_call_flow(calling_subscriber, called_subscriber):
    """Implement basic IMS voice call flow"""
    
    print(f"Starting voice call: {calling_subscriber.msisdn} -> {called_subscriber.msisdn}")
    
    # 1. Policy reservation (Gx)
    print("1. Policy reservation (Gx)")
    gx_request, gx_answer = voice_service.send_request(
        create_ccr_initial_message(calling_subscriber)
    )
    
    if gx_answer.result_code != DIAMETER_SUCCESS:
        print(f"Policy reservation failed: {gx_answer.result_code}")
        return False
    
    # 2. Media reservation (Rx)
    print("2. Media reservation (Rx)")
    rx_request, rx_answer = voice_service.send_request(
        create_aar_message(calling_subscriber, called_subscriber)
    )
    
    if rx_answer.result_code != DIAMETER_SUCCESS:
        print(f"Media reservation failed: {rx_answer.result_code}")
        return False
    
    # 3. Call establishment
    print("3. Call establishment")
    call_session = establish_call_session(calling_subscriber, called_subscriber)
    
    # 4. Call monitoring
    print("4. Call monitoring")
    monitor_call_session(call_session)
    
    # 5. Call termination
    print("5. Call termination")
    terminate_call_session(call_session)
    
    print(f"Voice call completed: {calling_subscriber.msisdn} -> {called_subscriber.msisdn}")
    return True
```

### Video Call Flow
```python
def video_call_flow(calling_subscriber, called_subscriber):
    """Implement IMS video call flow"""
    
    print(f"Starting video call: {calling_subscriber.msisdn} -> {called_subscriber.msisdn}")
    
    # 1. Policy reservation with video support
    print("1. Policy reservation with video support (Gx)")
    gx_request, gx_answer = voice_service.send_request(
        create_ccr_initial_message(calling_subscriber, media_type="video")
    )
    
    if gx_answer.result_code != DIAMETER_SUCCESS:
        print(f"Policy reservation failed: {gx_answer.result_code}")
        return False
    
    # 2. Media reservation for video
    print("2. Media reservation for video (Rx)")
    rx_request, rx_answer = voice_service.send_request(
        create_aar_message(calling_subscriber, called_subscriber, media_type="video")
    )
    
    if rx_answer.result_code != DIAMETER_SUCCESS:
        print(f"Media reservation failed: {rx_answer.result_code}")
        return False
    
    # 3. Video call establishment
    print("3. Video call establishment")
    video_session = establish_video_session(calling_subscriber, called_subscriber)
    
    # 4. Quality monitoring
    print("4. Quality monitoring")
    monitor_video_quality(video_session)
    
    # 5. Call termination
    print("5. Call termination")
    terminate_video_session(video_session)
    
    print(f"Video call completed: {calling_subscriber.msisdn} -> {called_subscriber.msisdn}")
    return True
```

### Conference Call Flow
```python
def conference_call_flow(initiator, participants):
    """Implement IMS conference call flow"""
    
    print(f"Starting conference call with {len(participants)} participants")
    
    # 1. Policy reservation for conference
    print("1. Policy reservation for conference (Gx)")
    gx_request, gx_answer = voice_service.send_request(
        create_ccr_initial_message(initiator, media_type="conference")
    )
    
    if gx_answer.result_code != DIAMETER_SUCCESS:
        print(f"Policy reservation failed: {gx_answer.result_code}")
        return False
    
    # 2. Media reservation for conference
    print("2. Media reservation for conference (Rx)")
    rx_request, rx_answer = voice_service.send_request(
        create_aar_message(initiator, participants, media_type="conference")
    )
    
    if rx_answer.result_code != DIAMETER_SUCCESS:
        print(f"Media reservation failed: {rx_answer.result_code}")
        return False
    
    # 3. Conference establishment
    print("3. Conference establishment")
    conference_session = establish_conference_session(initiator, participants)
    
    # 4. Conference management
    print("4. Conference management")
    manage_conference_session(conference_session)
    
    # 5. Conference termination
    print("5. Conference termination")
    terminate_conference_session(conference_session)
    
    print(f"Conference call completed with {len(participants)} participants")
    return True
```

## Call Quality Management

### Quality Monitoring
```python
def monitor_call_quality(session):
    """Monitor call quality and adjust resources"""
    
    while session.is_active():
        # Get current quality metrics
        quality_metrics = session.get_quality_metrics()
        
        # Check quality thresholds
        if quality_metrics["jitter"] > 50:  # High jitter
            print("High jitter detected, adjusting codec")
            session.adjust_codec("G.711")
        
        if quality_metrics["packet_loss"] > 5:  # High packet loss
            print("High packet loss detected, reducing bandwidth")
            session.reduce_bandwidth()
        
        if quality_metrics["latency"] > 200:  # High latency
            print("High latency detected, optimizing routing")
            session.optimize_routing()
        
        # Wait before next check
        time.sleep(10)
```

### Dynamic Quality Adjustment
```python
def adjust_call_quality(session, target_quality="HD"):
    """Dynamically adjust call quality"""
    
    current_quality = session.get_current_quality()
    
    if target_quality == "HD" and current_quality != "HD":
        # Upgrade to HD
        session.upgrade_to_hd()
        print("Call quality upgraded to HD")
    
    elif target_quality == "SD" and current_quality == "HD":
        # Downgrade to SD
        session.downgrade_to_sd()
        print("Call quality downgraded to SD")
    
    elif target_quality == "voice" and current_quality != "voice":
        # Switch to voice only
        session.switch_to_voice()
        print("Call switched to voice only")
```

## Performance Simulation

### Concurrent Call Simulation
```python
def simulate_concurrent_calls(subscribers, duration=300):
    """Simulate concurrent voice calls"""
    
    start_time = time.time()
    active_calls = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        # Start calls for all subscribers
        futures = []
        for i in range(0, len(subscribers), 2):
            if i + 1 < len(subscribers):
                calling_subscriber = subscribers[i]
                called_subscriber = subscribers[i + 1]
                
                future = executor.submit(
                    basic_voice_call_flow,
                    calling_subscriber,
                    called_subscriber
                )
                futures.append((calling_subscriber, called_subscriber, future))
        
        # Wait for calls to complete
        for calling_subscriber, called_subscriber, future in futures:
            try:
                result = future.result(timeout=60)
                if result:
                    active_calls[f"{calling_subscriber.msisdn}-{called_subscriber.msisdn}"] = {
                        "calling": calling_subscriber,
                        "called": called_subscriber,
                        "start_time": time.time()
                    }
                    print(f"Call started: {calling_subscriber.msisdn} -> {called_subscriber.msisdn}")
            except Exception as e:
                print(f"Failed to start call: {calling_subscriber.msisdn} -> {called_subscriber.msisdn}: {e}")
        
        # Simulate call duration
        while time.time() - start_time < duration:
            # Randomly modify calls
            for call_id in list(active_calls.keys()):
                if random.random() < 0.05:  # 5% chance per iteration
                    try:
                        call_info = active_calls[call_id]
                        modify_call_quality(call_info["calling"], call_info["called"])
                        print(f"Call quality modified: {call_id}")
                    except Exception as e:
                        print(f"Failed to modify call quality: {call_id}: {e}")
            
            time.sleep(10)  # Wait 10 seconds between iterations
        
        # Terminate all calls
        for call_id, call_info in active_calls.items():
            try:
                terminate_call_session(call_info["calling"], call_info["called"])
                print(f"Call terminated: {call_id}")
            except Exception as e:
                print(f"Failed to terminate call: {call_id}: {e}")
```

## Running the Example

### Basic Usage
```bash
# Run the comprehensive voice service example
python examples/voice_service_comprehensive.py
```

### Custom Configuration
```python
# Customize the example
def run_custom_voice_example():
    # Create custom IMS network
    ims_network = IMSNetwork(
        p_cscf="p-cscf.custom.ims.net",
        s_cscf="s-cscf.custom.ims.net",
        mgw="mgw.custom.ims.net"
    )
    
    # Create custom subscribers
    subscribers = [
        Subscriber("1111111111", "111111111111111", ims_network),
        Subscriber("2222222222", "222222222222222", ims_network)
    ]
    
    # Run voice call simulation
    simulate_concurrent_calls(subscribers, duration=600)
```

### Performance Testing
```python
# Run performance test
def run_voice_performance_test():
    # Create large number of subscribers
    subscribers = []
    for i in range(50):
        subscriber = Subscriber(
            msisdn=f"200000000{i:02d}",
            imsi=f"20000000000000{i:02d}",
            carrier=ims_network
        )
        subscribers.append(subscriber)
    
    # Run performance simulation
    metrics = simulate_concurrent_calls(subscribers, duration=600)
    
    # Print performance results
    print(f"Voice Performance Results:")
    print(f"  Total Calls: {metrics['total_calls']}")
    print(f"  Successful Calls: {metrics['successful_calls']}")
    print(f"  Failed Calls: {metrics['failed_calls']}")
    print(f"  Average Call Duration: {metrics['avg_call_duration']}s")
    print(f"  Quality Issues: {metrics['quality_issues']}")
```

## Expected Output

The example will demonstrate:

1. **IMS Network Setup**: PCEF, PCRF, and AF entities starting up
2. **Peer Connections**: Successful peer establishment
3. **Voice Call Flows**: Complete IMS voice call flows
4. **Video Call Flows**: HD video call scenarios
5. **Conference Calls**: Multi-participant conference calls
6. **Quality Management**: Dynamic quality adjustment
7. **Performance Metrics**: Real-time performance monitoring

## Key Learning Points

1. **IMS Architecture**: How VoiceService handles IMS network operations
2. **Gx-Rx Coordination**: Policy and media session coordination
3. **Call Quality Management**: Dynamic quality adjustment and monitoring
4. **Media Resource Management**: Efficient media resource allocation
5. **Real-World Scenarios**: Practical IMS call flow simulation
6. **Performance Optimization**: Concurrent call handling and resource management

## Next Steps

1. **Try the Example**: Run the comprehensive voice service example
2. **Modify Scenarios**: Customize call types, quality settings, and participants
3. **Performance Tuning**: Experiment with different performance parameters
4. **Explore Other Examples**: Check out [Data Service Comprehensive](data_service_comprehensive.md) and [Multi-Service Advanced](multi_service_advanced.md)
5. **API Reference**: Explore the [VoiceService API](../api/services/voice.md) for detailed documentation
