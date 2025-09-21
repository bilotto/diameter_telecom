# Message Processing

The message processing system in Diameter Telecom provides a sophisticated pipeline for handling Diameter messages with stage-based processing, error resilience, and performance optimization.

## Message Processing Pipeline

The library uses a stage-based processing pipeline that breaks complex operations into discrete, testable stages:

```
Message Input → Session Retrieval → Subscriber Identification → Cross-Application Binding → Business Logic → Response Generation
```

### Processing Stages

1. **Session Retrieval**: Find or create appropriate sessions
2. **Subscriber Identification**: Identify the subscriber from message data
3. **Cross-Application Binding**: Link sessions across different applications
4. **Business Logic**: Apply application-specific processing
5. **Response Generation**: Generate appropriate responses

## MessageProcessingPipeline

### Basic Usage
```python
from diameter_telecom.diameter.message_processing_pipeline import MessageProcessingPipeline
from diameter_telecom.diameter.message import DiameterMessage

# Create pipeline
pipeline = MessageProcessingPipeline()

# Process message
diameter_message = DiameterMessage(hex_string_or_message_object)
result = pipeline.process_message(diameter_message)

# Access processing result
if result.success:
    print(f"Message processed successfully: {result.response}")
else:
    print(f"Processing failed: {result.error}")
```

### Custom Pipeline Configuration
```python
# Create pipeline with custom configuration
pipeline = MessageProcessingPipeline(
    enable_session_retrieval=True,
    enable_subscriber_identification=True,
    enable_cross_application_binding=True,
    enable_business_logic=True,
    enable_response_generation=True
)

# Process message with custom context
context = MessageProcessingContext(
    session_manager=session_manager,
    subscriber_manager=subscriber_manager,
    application_config=app_config
)

result = pipeline.process_message(diameter_message, context)
```

## MessageProcessingContext

### Context Creation
```python
from diameter_telecom.diameter.message_processing_context import MessageProcessingContext

# Create processing context
context = MessageProcessingContext(
    session_manager=session_manager,
    subscriber_manager=subscriber_manager,
    application_config={
        "gx": gx_config,
        "rx": rx_config,
        "sy": sy_config
    },
    processing_options={
        "enable_caching": True,
        "enable_logging": True,
        "timeout": 30
    }
)

# Add custom data to context
context.add_data("custom_field", custom_value)
context.add_data("processing_metadata", metadata)
```

### Context Usage
```python
# Access context data
session_manager = context.session_manager
subscriber_manager = context.subscriber_manager
app_config = context.application_config

# Get custom data
custom_value = context.get_data("custom_field")
metadata = context.get_data("processing_metadata")

# Update context
context.update_data("processing_status", "in_progress")
```

## Stage-Based Processing

### Session Retrieval Stage
```python
class SessionRetrievalStage:
    def process(self, message, context):
        """Retrieve or create appropriate sessions"""
        session_id = message.get_session_id()
        session = context.session_manager.get_session_by_id(session_id)
        
        if not session:
            # Create new session
            session = self.create_session(message, context)
            context.session_manager.add_session(session)
        
        context.add_data("session", session)
        return True
```

### Subscriber Identification Stage
```python
class SubscriberIdentificationStage:
    def process(self, message, context):
        """Identify subscriber from message data"""
        subscriber = self.identify_subscriber(message)
        
        if not subscriber:
            # Create new subscriber
            subscriber = self.create_subscriber(message)
            context.subscriber_manager.add_subscriber(subscriber)
        
        context.add_data("subscriber", subscriber)
        return True
```

### Cross-Application Binding Stage
```python
class CrossApplicationBindingStage:
    def process(self, message, context):
        """Link sessions across different applications"""
        session = context.get_data("session")
        subscriber = context.get_data("subscriber")
        
        # Bind to related sessions
        if session.type == "RxSession":
            gx_session = subscriber.get_session("GxSession")
            if gx_session:
                session.bind_to_gx_session(gx_session)
        
        elif session.type == "SySession":
            gx_session = subscriber.get_session("GxSession")
            if gx_session:
                session.bind_to_gx_session(gx_session)
        
        return True
```

### Business Logic Stage
```python
class BusinessLogicStage:
    def process(self, message, context):
        """Apply application-specific business logic"""
        session = context.get_data("session")
        subscriber = context.get_data("subscriber")
        
        # Apply business logic based on application
        if message.app_id == APP_3GPP_GX:
            self.apply_gx_logic(message, session, subscriber, context)
        elif message.app_id == APP_3GPP_RX:
            self.apply_rx_logic(message, session, subscriber, context)
        elif message.app_id == APP_3GPP_SY:
            self.apply_sy_logic(message, session, subscriber, context)
        
        return True
```

## Custom Processing Logic

### Custom Stage Implementation
```python
class CustomProcessingStage:
    def __init__(self, custom_logic):
        self.custom_logic = custom_logic
    
    def process(self, message, context):
        """Custom processing logic"""
        try:
            # Apply custom logic
            result = self.custom_logic(message, context)
            
            # Update context with result
            context.add_data("custom_result", result)
            
            return True
        except Exception as e:
            context.add_data("custom_error", str(e))
            return False
```

### Custom Pipeline
```python
class CustomPipeline(MessageProcessingPipeline):
    def __init__(self):
        super().__init__()
        
        # Add custom stages
        self.add_stage("custom_validation", CustomValidationStage())
        self.add_stage("custom_processing", CustomProcessingStage(custom_logic))
        self.add_stage("custom_response", CustomResponseStage())
    
    def process_message(self, message, context):
        """Custom message processing"""
        # Pre-processing
        self.pre_process(message, context)
        
        # Standard processing
        result = super().process_message(message, context)
        
        # Post-processing
        self.post_process(message, context, result)
        
        return result
```

## Error Handling and Resilience

### Safe AVP Parsing
```python
def safe_parse_avp(message, avp_code):
    """Safely parse AVP with bounds checking"""
    try:
        avp = message.get_avp(avp_code)
        if avp and avp.data:
            return avp.data.decode('utf-8')
        return None
    except (IndexError, UnicodeDecodeError, AttributeError) as e:
        logger.warning(f"Failed to parse AVP {avp_code}: {e}")
        return None
```

### Error Recovery
```python
class ErrorRecoveryStage:
    def process(self, message, context):
        """Handle processing errors and recovery"""
        try:
            # Attempt processing
            result = self.attempt_processing(message, context)
            return result
        except Exception as e:
            # Log error
            logger.error(f"Processing error: {e}")
            
            # Attempt recovery
            if self.can_recover(e):
                return self.recover_from_error(message, context, e)
            else:
                # Generate error response
                return self.generate_error_response(message, context, e)
```

### Graceful Degradation
```python
class GracefulDegradationStage:
    def process(self, message, context):
        """Handle graceful degradation when services are unavailable"""
        try:
            # Attempt full processing
            return self.full_processing(message, context)
        except ServiceUnavailableError:
            # Fall back to basic processing
            return self.basic_processing(message, context)
        except Exception as e:
            # Log error and continue
            logger.error(f"Processing error: {e}")
            return self.minimal_processing(message, context)
```

## Performance Optimization

### Caching
```python
class CachingStage:
    def __init__(self, cache_backend):
        self.cache = cache_backend
    
    def process(self, message, context):
        """Use caching for performance optimization"""
        cache_key = self.generate_cache_key(message)
        
        # Check cache first
        cached_result = self.cache.get(cache_key)
        if cached_result:
            context.add_data("cached_result", cached_result)
            return True
        
        # Process message
        result = self.process_message(message, context)
        
        # Cache result
        self.cache.set(cache_key, result, ttl=300)  # 5 minutes
        
        return result
```

### Parallel Processing
```python
import concurrent.futures

class ParallelProcessingStage:
    def process(self, message, context):
        """Process message in parallel when possible"""
        # Identify parallelizable operations
        operations = self.identify_parallel_operations(message, context)
        
        # Execute in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for operation in operations:
                future = executor.submit(operation.execute, message, context)
                futures.append(future)
            
            # Collect results
            results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Parallel processing error: {e}")
        
        # Combine results
        combined_result = self.combine_results(results)
        context.add_data("parallel_result", combined_result)
        
        return True
```

### Memory Management
```python
class MemoryManagementStage:
    def process(self, message, context):
        """Manage memory usage during processing"""
        # Monitor memory usage
        memory_usage = self.get_memory_usage()
        
        if memory_usage > self.memory_threshold:
            # Cleanup old data
            self.cleanup_old_data(context)
            
            # Force garbage collection
            import gc
            gc.collect()
        
        # Process message
        result = self.process_message(message, context)
        
        # Cleanup processing data
        self.cleanup_processing_data(context)
        
        return result
```

## Message State Tracking

### Message History
```python
class MessageHistoryStage:
    def process(self, message, context):
        """Track message history and state"""
        # Add to message history
        context.add_message_to_history(message)
        
        # Update message state
        message.update_state("processing")
        
        # Track processing metrics
        self.track_processing_metrics(message, context)
        
        return True
```

### State Management
```python
class StateManagementStage:
    def process(self, message, context):
        """Manage message and session state"""
        # Update message state
        message.state = MessageState.PROCESSING
        
        # Update session state if applicable
        session = context.get_data("session")
        if session:
            session.update_state(message)
        
        # Update subscriber state
        subscriber = context.get_data("subscriber")
        if subscriber:
            subscriber.update_state(message)
        
        return True
```

## Custom Message Processing

### Application-Specific Processing
```python
class GxMessageProcessor:
    def process(self, message, context):
        """Process Gx application messages"""
        if message.command_code == CCR_INITIAL:
            return self.process_ccr_initial(message, context)
        elif message.command_code == CCR_UPDATE:
            return self.process_ccr_update(message, context)
        elif message.command_code == CCR_TERMINATION:
            return self.process_ccr_termination(message, context)
        else:
            return self.process_unknown_command(message, context)
```

### Custom Response Generation
```python
class CustomResponseGenerator:
    def generate_response(self, message, context):
        """Generate custom responses based on context"""
        # Get processing result
        result = context.get_data("processing_result")
        
        # Generate response based on result
        if result.success:
            response = self.generate_success_response(message, result)
        else:
            response = self.generate_error_response(message, result)
        
        # Add custom headers
        response.add_custom_header("X-Custom-Header", "custom-value")
        
        return response
```

## Best Practices

### 1. Use Stage-Based Processing
```python
# ✅ Good: Stage-based processing
pipeline = MessageProcessingPipeline()
pipeline.add_stage("validation", ValidationStage())
pipeline.add_stage("processing", ProcessingStage())
pipeline.add_stage("response", ResponseStage())

# ❌ Avoid: Monolithic processing
def process_message(message):
    # All processing in one function
    validate_message(message)
    process_message(message)
    generate_response(message)
```

### 2. Handle Errors Gracefully
```python
# ✅ Good: Error handling
try:
    result = pipeline.process_message(message, context)
    if not result.success:
        logger.error(f"Processing failed: {result.error}")
        return generate_error_response(message, result.error)
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return generate_error_response(message, "Internal error")

# ❌ Avoid: Ignoring errors
result = pipeline.process_message(message, context)
# No error handling
```

### 3. Use Context for Data Sharing
```python
# ✅ Good: Context-based data sharing
context.add_data("session", session)
context.add_data("subscriber", subscriber)
result = pipeline.process_message(message, context)

# ❌ Avoid: Global variables
global_session = session
global_subscriber = subscriber
result = pipeline.process_message(message)
```

### 4. Optimize Performance
```python
# ✅ Good: Performance optimization
pipeline.enable_caching = True
pipeline.enable_parallel_processing = True
pipeline.memory_management = True

# ❌ Avoid: No optimization
pipeline = MessageProcessingPipeline()
# No performance considerations
```

## Common Patterns

### Message Validation
```python
class MessageValidationStage:
    def process(self, message, context):
        """Validate message before processing"""
        # Check message format
        if not message.is_valid():
            context.add_data("validation_error", "Invalid message format")
            return False
        
        # Check required AVPs
        required_avps = ["Session-Id", "Origin-Host", "Origin-Realm"]
        for avp_code in required_avps:
            if not message.has_avp(avp_code):
                context.add_data("validation_error", f"Missing required AVP: {avp_code}")
                return False
        
        return True
```

### Session Coordination
```python
class SessionCoordinationStage:
    def process(self, message, context):
        """Coordinate sessions across applications"""
        session = context.get_data("session")
        subscriber = context.get_data("subscriber")
        
        # Coordinate with related sessions
        if session.type == "GxSession":
            # Update related Rx and Sy sessions
            self.update_related_sessions(session, subscriber)
        elif session.type == "RxSession":
            # Coordinate with Gx session
            gx_session = subscriber.get_session("GxSession")
            if gx_session:
                self.coordinate_with_gx_session(session, gx_session)
        
        return True
```

### Response Generation
```python
class ResponseGenerationStage:
    def process(self, message, context):
        """Generate appropriate response"""
        # Get processing result
        result = context.get_data("processing_result")
        
        # Generate response
        response = self.generate_response(message, result)
        
        # Add response to context
        context.add_data("response", response)
        
        return True
```

## Next Steps

1. **Try Examples**: Check out the [message processing examples](../examples/debug_routing.md) to see processing in action
2. **Advanced Usage**: Explore [Advanced Usage](advanced.md) for custom implementations
3. **Session Management**: Understand [Session Management](sessions.md) for complex scenarios
4. **API Reference**: Explore the [API documentation](../api/processing/pipeline.md) for detailed class information
