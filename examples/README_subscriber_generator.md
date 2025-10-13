# Subscriber Generator Example

This example demonstrates how to use the new `SubscriberGenerator` functionality in the `Carrier` class to automatically generate unique MSISDN and IMSI pairs for subscribers.

## Features

- **Configurable Lengths**: Set custom MSISDN and IMSI lengths
- **Thread Safety**: Uses threading locks to prevent race conditions
- **Standards Compliance**: Follows telecommunications standards for identifier formats
- **Batch Generation**: Create multiple subscribers efficiently
- **Statistics**: Monitor generator state and usage

## Basic Usage

```python
from diameter_telecom import Carrier

# Create a carrier with default lengths (MSISDN: 13, IMSI: 15)
carrier = Carrier(
    name="ZetaTel",
    mcc_mnc=["72488"],  # Brazil, Vivo
    country_code="55"
)

# Generate a subscriber with automatic MSISDN/IMSI
subscriber = carrier.create_subscriber()
print(f"MSISDN: {subscriber.msisdn}, IMSI: {subscriber.imsi}")
```

## Custom Lengths

```python
# Create a carrier with custom lengths
carrier = Carrier(
    name="TestCarrier",
    mcc_mnc=["310260"],  # US, T-Mobile
    country_code="1",
    msisdn_length=11,    # Custom MSISDN length
    imsi_length=12       # Custom IMSI length
)

# Generate subscribers with custom lengths
subscriber = carrier.create_subscriber()
print(f"MSISDN: {subscriber.msisdn}, IMSI: {subscriber.imsi}")
```

## Custom Identifiers

```python
# Create a subscriber with specific identifiers
subscriber = carrier.create_subscriber(
    msisdn="5511999999999",
    imsi="724880000000000"
)
```

## Batch Generation

```python
# Create multiple subscribers at once
subscribers = carrier.create_subscribers_batch(10)
for i, subscriber in enumerate(subscribers):
    print(f"Subscriber {i+1}: MSISDN={subscriber.msisdn}, IMSI={subscriber.imsi}")
```

## Generator Statistics

```python
# Get generator statistics
stats = carrier.get_subscriber_generator_stats()
print("Generator stats:")
for key, value in stats.items():
    print(f"  {key}: {value}")
```

## Format Details

### MSISDN Format
- **Structure**: `<country_code><subscriber_number>`
- **Example**: `5536391264684` (country_code=55, subscriber_number=36391264684)
- **Configurable**: Total length can be set via `msisdn_length` parameter

### IMSI Format
- **Structure**: `<MCC><MNC><MSIN>`
- **Example**: `724885514640486` (MCC=724, MNC=88, MSIN=5514640486)
- **Configurable**: Total length can be set via `imsi_length` parameter

## MCC/MNC Support

The generator supports both 5-digit and 6-digit MCC/MNC formats:

- **5-digit**: 3-digit MCC + 2-digit MNC (e.g., "72488")
- **6-digit**: 3-digit MCC + 3-digit MNC (e.g., "310260")

## Thread Safety

The generator is thread-safe and can be used in concurrent environments:

```python
import threading

def create_subscribers(carrier, count):
    for _ in range(count):
        subscriber = carrier.create_subscriber()
        print(f"Thread {threading.current_thread().name}: {subscriber.msisdn}")

# Create multiple threads
threads = []
for i in range(3):
    thread = threading.Thread(target=create_subscribers, args=(carrier, 5))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()
```

## Running the Example

To run the complete example:

```bash
python examples/carrier_subscriber_generator_example.py
```

This will demonstrate all the features mentioned above with various carrier configurations and subscriber generation scenarios.
