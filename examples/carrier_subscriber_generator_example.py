#!/usr/bin/env python3
"""
Example demonstrating the Carrier class with SubscriberGenerator functionality.

This example shows how to:
1. Create carriers with different MSISDN and IMSI lengths
2. Generate subscribers with automatic MSISDN/IMSI generation
3. Create subscribers with custom identifiers
4. Generate multiple subscribers in batch
5. View generator statistics
"""

import sys
import os

# Add the src directory to the path so we can import diameter_telecom
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from diameter_telecom import Carrier, Subscriber

def main():
    print("=== Carrier Subscriber Generator Example ===\n")
    
    # Example 1: Default lengths (MSISDN: 13, IMSI: 15)
    print("1. Creating carrier with default lengths (MSISDN: 13, IMSI: 15)")
    carrier1 = Carrier(
        name="ZetaTel",
        mcc_mnc=["72488"],  # Brazil, Vivo
        country_code="55"
    )
    
    print(f"Carrier: {carrier1.name}")
    print(f"MCC/MNC: {carrier1.mcc_mnc}")
    print(f"Country Code: {carrier1.country_code}")
    print(f"MSISDN Length: {carrier1.msisdn_length}")
    print(f"IMSI Length: {carrier1.imsi_length}")
    
    # Generate a few subscribers
    print("\nGenerating subscribers:")
    for i in range(3):
        subscriber = carrier1.create_subscriber()
        print(f"  Subscriber {i+1}: MSISDN={subscriber.msisdn}, IMSI={subscriber.imsi}")
    
    # Example 2: Custom lengths
    print("\n" + "="*60)
    print("2. Creating carrier with custom lengths (MSISDN: 11, IMSI: 12)")
    carrier2 = Carrier(
        name="TestCarrier",
        mcc_mnc=["310260"],  # US, T-Mobile
        country_code="1",
        msisdn_length=11,
        imsi_length=12
    )
    
    print(f"Carrier: {carrier2.name}")
    print(f"MCC/MNC: {carrier2.mcc_mnc}")
    print(f"Country Code: {carrier2.country_code}")
    print(f"MSISDN Length: {carrier2.msisdn_length}")
    print(f"IMSI Length: {carrier2.imsi_length}")
    
    # Generate a few subscribers
    print("\nGenerating subscribers:")
    for i in range(3):
        subscriber = carrier2.create_subscriber()
        print(f"  Subscriber {i+1}: MSISDN={subscriber.msisdn}, IMSI={subscriber.imsi}")
    
    # Example 3: Custom identifiers
    print("\n" + "="*60)
    print("3. Creating subscribers with custom identifiers")
    custom_subscriber = carrier1.create_subscriber(
        msisdn="5511999999999",
        imsi="724880000000000"
    )
    print(f"Custom subscriber: MSISDN={custom_subscriber.msisdn}, IMSI={custom_subscriber.imsi}")
    
    # Example 4: Batch generation
    print("\n" + "="*60)
    print("4. Batch generation of subscribers")
    batch_subscribers = carrier1.create_subscribers_batch(5)
    print(f"Generated {len(batch_subscribers)} subscribers:")
    for i, subscriber in enumerate(batch_subscribers):
        print(f"  Batch {i+1}: MSISDN={subscriber.msisdn}, IMSI={subscriber.imsi}")
    
    # Example 5: Generator statistics
    print("\n" + "="*60)
    print("5. Generator statistics")
    stats = carrier1.get_subscriber_generator_stats()
    print("Generator stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Example 6: Different MCC/MNC formats
    print("\n" + "="*60)
    print("6. Testing different MCC/MNC formats")
    
    # 5-digit format (3-digit MCC + 2-digit MNC)
    carrier_5digit = Carrier(
        name="Carrier5Digit",
        mcc_mnc=["72488"],  # 5 digits
        country_code="55",
        msisdn_length=12,
        imsi_length=14
    )
    
    # 6-digit format (3-digit MCC + 3-digit MNC)
    carrier_6digit = Carrier(
        name="Carrier6Digit",
        mcc_mnc=["310260"],  # 6 digits
        country_code="1",
        msisdn_length=11,
        imsi_length=15
    )
    
    print("5-digit MCC/MNC (72488):")
    sub1 = carrier_5digit.create_subscriber()
    print(f"  MSISDN={sub1.msisdn}, IMSI={sub1.imsi}")
    
    print("6-digit MCC/MNC (310260):")
    sub2 = carrier_6digit.create_subscriber()
    print(f"  MSISDN={sub2.msisdn}, IMSI={sub2.imsi}")
    
    print("\n=== Example completed successfully! ===")

if __name__ == "__main__":
    main()
