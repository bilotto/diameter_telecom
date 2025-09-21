# Advanced Usage

This guide covers advanced features, performance optimization, and custom implementations in Diameter Telecom.

## Performance Optimization

### Memory Management
```python
from diameter_telecom.diameter.session_manager import SessionManager

# Configure memory management
session_manager = SessionManager(
    max_sessions=10000,
    cleanup_interval=300,  # 5 minutes
    memory_threshold=0.8   # 80% memory usage
)

# Enable automatic cleanup
session_manager.enable_automatic_cleanup = True

# Monitor memory usage
memory_stats = session_manager.get_memory_statistics()
print(f"Memory usage: {memory_stats['usage']} MB")
print(f"Session count: {memory_stats['session_count']}")
```

### Caching Strategies
```python
import redis
from diameter_telecom.diameter.session_manager import SessionManager

# Redis-based caching
redis_client = redis.Redis(host='localhost', port=6379, db=0)

class CachedSessionManager(SessionManager):
    def __init__(self, redis_client):
        super().__init__()
        self.redis = redis_client
    
    def get_session(self, session_id):
        # Check cache first
        cached_session = self.redis.get(f"session:{session_id}")
        if cached_session:
            return self.deserialize_session(cached_session)
        
        # Fall back to database
        session = super().get_session(session_id)
        if session:
            # Cache session
            self.redis.setex(f"session:{session_id}", 3600, self.serialize_session(session))
        
        return session
```

### Parallel Processing
```python
import concurrent.futures
from diameter_telecom.diameter.message_processing_pipeline import MessageProcessingPipeline

class ParallelProcessingPipeline(MessageProcessingPipeline):
    def __init__(self, max_workers=4):
        super().__init__()
        self.max_workers = max_workers
    
    def process_messages(self, messages):
        """Process multiple messages in parallel"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for message in messages:
                future = executor.submit(self.process_message, message)
                futures.append(future)
            
            results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Parallel processing error: {e}")
            
            return results
```

## Custom Implementations

### Custom Service
```python
from diameter_telecom.services.service import Service

class CustomService(Service):
    def __init__(self, pcef, custom_entity):
        super().__init__(pcef=pcef)
        self.custom_entity = custom_entity
        self.custom_config = {}
    
    def send_request(self, message, timeout=10):
        """Custom request handling"""
        # Custom routing logic
        if message.app_id == CUSTOM_APP_ID:
            return self.custom_entity.send_request(message, timeout)
        else:
            return super().send_request(message, timeout)
    
    def configure(self, config):
        """Configure custom service"""
        self.custom_config.update(config)
    
    def get_statistics(self):
        """Get custom service statistics"""
        stats = super().get_statistics()
        stats.update({
            "custom_requests": self.custom_entity.request_count,
            "custom_errors": self.custom_entity.error_count
        })
        return stats
```

### Custom Entity
```python
from diameter_telecom.entities_3gpp._entity import Entity

class CustomEntity(Entity):
    def __init__(self, origin_host, realm_name, ip_addresses, tcp_port):
        super().__init__(origin_host, realm_name, ip_addresses, tcp_port)
        self.custom_applications = {}
        self.custom_handlers = {}
    
    def setup_custom_app(self, app_id, handler):
        """Setup custom application"""
        self.custom_applications[app_id] = app_id
        self.custom_handlers[app_id] = handler
    
    def handle_custom_request(self, request, answer):
        """Handle custom requests"""
        app_id = request.app_id
        if app_id in self.custom_handlers:
            return self.custom_handlers[app_id](request, answer)
        else:
            return self.handle_unknown_request(request, answer)
```

### Custom Session
```python
from diameter_telecom.diameter.session import Session

class CustomSession(Session):
    def __init__(self, session_id, subscriber, custom_data=None):
        super().__init__(session_id, subscriber)
        self.custom_data = custom_data or {}
        self.custom_state = "created"
    
    def update_custom_data(self, key, value):
        """Update custom session data"""
        self.custom_data[key] = value
    
    def get_custom_data(self, key):
        """Get custom session data"""
        return self.custom_data.get(key)
    
    def process_custom_logic(self, message):
        """Process custom business logic"""
        # Custom processing logic
        result = self.apply_custom_logic(message)
        return result
```

## Network Topology Management

### Multi-Carrier Network
```python
class MultiCarrierNetwork:
    def __init__(self):
        self.carriers = {}
        self.routing_table = {}
    
    def add_carrier(self, carrier_id, carrier_config):
        """Add carrier to network"""
        self.carriers[carrier_id] = carrier_config
        
        # Create carrier entities
        pcef = PCEF(
            origin_host=f"pcef.{carrier_id}.net",
            realm_name=f"{carrier_id}.net",
            ip_addresses=carrier_config["ip_addresses"],
            tcp_port=carrier_config["tcp_port"]
        )
        
        pcrf = PCRF(
            origin_host=f"pcrf.{carrier_id}.net",
            realm_name=f"{carrier_id}.net",
            ip_addresses=carrier_config["pcrf_ips"],
            tcp_port=carrier_config["pcrf_port"]
        )
        
        # Setup carrier network
        self.setup_carrier_network(carrier_id, pcef, pcrf)
    
    def setup_carrier_network(self, carrier_id, pcef, pcrf):
        """Setup carrier network topology"""
        # Setup peer relationships
        pcef.add_node_as_peer(pcrf.node, app_id=APP_3GPP_GX, initiate_connection=True)
        pcrf.add_node_as_peer(pcef.node, app_id=APP_3GPP_GX, initiate_connection=False)
        
        # Setup applications
        pcef.setup_gx_app()
        pcrf.setup_gx_app()
        
        # Start entities
        pcef.start()
        pcrf.start()
        
        # Store in routing table
        self.routing_table[carrier_id] = {
            "pcef": pcef,
            "pcrf": pcrf
        }
    
    def route_message(self, message, carrier_id):
        """Route message to specific carrier"""
        if carrier_id in self.routing_table:
            carrier = self.routing_table[carrier_id]
            return carrier["pcrf"].send_request(message)
        else:
            raise ValueError(f"Unknown carrier: {carrier_id}")
```

### Load Balancing
```python
class LoadBalancer:
    def __init__(self, entities):
        self.entities = entities
        self.current_index = 0
        self.health_checks = {}
    
    def get_next_entity(self):
        """Get next available entity using round-robin"""
        available_entities = [e for e in self.entities if self.is_healthy(e)]
        
        if not available_entities:
            raise Exception("No healthy entities available")
        
        entity = available_entities[self.current_index % len(available_entities)]
        self.current_index += 1
        
        return entity
    
    def is_healthy(self, entity):
        """Check entity health"""
        if entity.origin_host in self.health_checks:
            last_check = self.health_checks[entity.origin_host]
            if time.time() - last_check["timestamp"] < 30:  # 30 seconds
                return last_check["healthy"]
        
        # Perform health check
        try:
            entity.ping()
            self.health_checks[entity.origin_host] = {
                "timestamp": time.time(),
                "healthy": True
            }
            return True
        except Exception:
            self.health_checks[entity.origin_host] = {
                "timestamp": time.time(),
                "healthy": False
            }
            return False
```

## Monitoring and Observability

### Metrics Collection
```python
import time
from collections import defaultdict

class MetricsCollector:
    def __init__(self):
        self.metrics = defaultdict(list)
        self.counters = defaultdict(int)
        self.timers = {}
    
    def increment_counter(self, metric_name, value=1):
        """Increment counter metric"""
        self.counters[metric_name] += value
    
    def record_timer(self, metric_name, duration):
        """Record timer metric"""
        self.metrics[metric_name].append(duration)
    
    def start_timer(self, metric_name):
        """Start timer for metric"""
        self.timers[metric_name] = time.time()
    
    def end_timer(self, metric_name):
        """End timer and record duration"""
        if metric_name in self.timers:
            duration = time.time() - self.timers[metric_name]
            self.record_timer(metric_name, duration)
            del self.timers[metric_name]
    
    def get_metrics(self):
        """Get all metrics"""
        return {
            "counters": dict(self.counters),
            "timers": {
                name: {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values)
                }
                for name, values in self.metrics.items()
            }
        }
```

### Health Monitoring
```python
class HealthMonitor:
    def __init__(self, entities):
        self.entities = entities
        self.health_status = {}
        self.last_checks = {}
    
    def check_health(self):
        """Check health of all entities"""
        for entity in self.entities:
            try:
                # Perform health check
                start_time = time.time()
                entity.ping()
                response_time = time.time() - start_time
                
                self.health_status[entity.origin_host] = {
                    "status": "healthy",
                    "response_time": response_time,
                    "last_check": time.time()
                }
            except Exception as e:
                self.health_status[entity.origin_host] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": time.time()
                }
    
    def get_health_status(self):
        """Get current health status"""
        return self.health_status
    
    def get_unhealthy_entities(self):
        """Get list of unhealthy entities"""
        return [
            host for host, status in self.health_status.items()
            if status["status"] == "unhealthy"
        ]
```

### Logging Configuration
```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Create structured formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def log_message_processing(self, message, context, result):
        """Log message processing with structured data"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": message.get_message_id(),
            "command_code": message.command_code,
            "app_id": message.app_id,
            "session_id": message.get_session_id(),
            "subscriber": context.get_data("subscriber").msisdn if context.get_data("subscriber") else None,
            "processing_time": result.processing_time,
            "success": result.success,
            "error": result.error if not result.success else None
        }
        
        self.logger.info(json.dumps(log_data))
    
    def log_session_event(self, session, event_type, data=None):
        """Log session events"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "session_id": session.session_id,
            "session_type": session.__class__.__name__,
            "subscriber": session.subscriber.msisdn,
            "data": data or {}
        }
        
        self.logger.info(json.dumps(log_data))
```

## Security and Authentication

### Message Authentication
```python
import hmac
import hashlib

class MessageAuthenticator:
    def __init__(self, secret_key):
        self.secret_key = secret_key
    
    def authenticate_message(self, message):
        """Authenticate message using HMAC"""
        # Create message digest
        message_digest = self.create_message_digest(message)
        
        # Generate HMAC
        hmac_signature = hmac.new(
            self.secret_key.encode(),
            message_digest.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Add authentication AVP
        message.add_avp("Message-Authentication", hmac_signature)
        
        return message
    
    def verify_message(self, message):
        """Verify message authentication"""
        # Extract HMAC signature
        auth_avp = message.get_avp("Message-Authentication")
        if not auth_avp:
            return False
        
        received_signature = auth_avp.data.decode()
        
        # Recreate message digest
        message_digest = self.create_message_digest(message)
        
        # Generate expected HMAC
        expected_signature = hmac.new(
            self.secret_key.encode(),
            message_digest.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(received_signature, expected_signature)
    
    def create_message_digest(self, message):
        """Create message digest for authentication"""
        # Create digest from message components
        components = [
            str(message.command_code),
            str(message.app_id),
            message.get_session_id(),
            message.get_origin_host(),
            message.get_origin_realm()
        ]
        
        return "|".join(components)
```

### Access Control
```python
class AccessController:
    def __init__(self, access_rules):
        self.access_rules = access_rules
    
    def check_access(self, message, context):
        """Check if message is allowed"""
        # Extract request information
        origin_host = message.get_origin_host()
        app_id = message.app_id
        command_code = message.command_code
        
        # Check access rules
        for rule in self.access_rules:
            if self.matches_rule(rule, origin_host, app_id, command_code):
                return rule["allowed"]
        
        # Default deny
        return False
    
    def matches_rule(self, rule, origin_host, app_id, command_code):
        """Check if message matches access rule"""
        # Check origin host
        if "origin_hosts" in rule:
            if origin_host not in rule["origin_hosts"]:
                return False
        
        # Check application ID
        if "app_ids" in rule:
            if app_id not in rule["app_ids"]:
                return False
        
        # Check command code
        if "command_codes" in rule:
            if command_code not in rule["command_codes"]:
                return False
        
        return True
```

## Testing and Validation

### Unit Testing
```python
import unittest
from unittest.mock import Mock, patch

class TestDiameterTelecom(unittest.TestCase):
    def setUp(self):
        """Setup test environment"""
        self.pcef = PCEF("pcef.test.net", "test.net", ["127.0.0.1"], tcp_port=3868)
        self.pcrf = PCRF("pcrf.test.net", "test.net", ["127.0.0.1"], tcp_port=3869)
        self.session_manager = SessionManager()
    
    def test_session_creation(self):
        """Test session creation"""
        subscriber = Subscriber(msisdn="1234567890", imsi="123456789012345")
        session = GxSession("test-session", subscriber)
        
        self.assertEqual(session.session_id, "test-session")
        self.assertEqual(session.subscriber, subscriber)
        self.assertEqual(session.state, SessionState.CREATED)
    
    def test_message_processing(self):
        """Test message processing"""
        # Mock message
        message = Mock()
        message.get_session_id.return_value = "test-session"
        message.app_id = APP_3GPP_GX
        message.command_code = CCR_INITIAL
        
        # Process message
        result = self.session_manager.process_diameter_message(message)
        
        self.assertTrue(result.success)
    
    @patch('diameter_telecom.entities_3gpp.pcrf.PCRF.start')
    def test_entity_startup(self, mock_start):
        """Test entity startup"""
        self.pcrf.start()
        mock_start.assert_called_once()
```

### Integration Testing
```python
class TestIntegration(unittest.TestCase):
    def setUp(self):
        """Setup integration test environment"""
        self.network = MultiCarrierNetwork()
        self.network.add_carrier("carrier1", {
            "ip_addresses": ["127.0.0.1"],
            "tcp_port": 3868,
            "pcrf_ips": ["127.0.0.1"],
            "pcrf_port": 3869
        })
    
    def test_end_to_end_flow(self):
        """Test end-to-end message flow"""
        # Create subscriber
        subscriber = Subscriber(msisdn="1234567890", imsi="123456789012345")
        
        # Create message
        message = create_ccr_initial_message(subscriber)
        
        # Route message
        result = self.network.route_message(message, "carrier1")
        
        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.response.command_code, CCA_INITIAL)
```

## Deployment and Operations

### Docker Deployment
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY src/ ./src/
COPY examples/ ./examples/

# Set environment variables
ENV PYTHONPATH=/app/src
ENV DIAMETER_TELECOM_CONFIG=/app/config.yaml

# Expose ports
EXPOSE 3868 3869 3870 3871

# Start application
CMD ["python", "examples/data_service_comprehensive.py"]
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: diameter-telecom
spec:
  replicas: 3
  selector:
    matchLabels:
      app: diameter-telecom
  template:
    metadata:
      labels:
        app: diameter-telecom
    spec:
      containers:
      - name: diameter-telecom
        image: diameter-telecom:latest
        ports:
        - containerPort: 3868
        - containerPort: 3869
        - containerPort: 3870
        - containerPort: 3871
        env:
        - name: DIAMETER_TELECOM_CONFIG
          value: "/app/config.yaml"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### Configuration Management
```python
import yaml
from pathlib import Path

class ConfigManager:
    def __init__(self, config_path):
        self.config_path = Path(config_path)
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def get_entity_config(self, entity_type):
        """Get configuration for entity type"""
        return self.config.get("entities", {}).get(entity_type, {})
    
    def get_network_config(self):
        """Get network configuration"""
        return self.config.get("network", {})
    
    def get_security_config(self):
        """Get security configuration"""
        return self.config.get("security", {})
```

## Next Steps

1. **Try Examples**: Check out the [advanced examples](../examples/multi_service_advanced.md) to see advanced features in action
2. **Performance Tuning**: Explore performance optimization techniques
3. **Custom Implementations**: Build custom services and entities
4. **API Reference**: Explore the [API documentation](../api/core/subscriber.md) for detailed class information
