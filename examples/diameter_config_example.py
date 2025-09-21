#!/usr/bin/env python3
"""
Example showing the new DiameterConfig class usage.
Demonstrates how to create explicit, intuitive service configurations.
"""

from diameter_telecom import *
from diameter_telecom.services.diameter_config import DiameterConfig, create_diameter_config_from_entities

def example_manual_config():
    """Example of manually creating DiameterConfig."""
    print("=== Manual DiameterConfig Creation ===")
    
    # Create entities
    pcef = PCEF(origin_host="pcef-0.pcef.realm", realm_name="pcef.realm")
    ocs = OCS(origin_host="ocs-0.ocs.realm", realm_name="ocs.realm")
    
    # Create explicit configuration
    config = DiameterConfig()
    config.set_gx_routing(
        origin_realm="pcef.realm",
        destination_realm="pcrf.realm"  # Target PCRF realm
    )
    config.set_sy_routing(
        origin_realm="ocs.realm", 
        destination_realm="pcrf.realm"  # Target PCRF realm
    )
    
    print(f"Gx config: {config.get_app_config(16777238)}")
    print(f"Sy config: {config.get_app_config(16777302)}")
    
    # Create service with explicit config
    data_service = DataService(pcef=pcef, ocs=ocs, diameter_config=config)
    print(f"Created DataService with explicit config")

def example_auto_config():
    """Example of auto-creating DiameterConfig from entities."""
    print("\n=== Auto DiameterConfig Creation ===")
    
    # Create entities
    pcef = PCEF(origin_host="pcef-0.pcef.realm", realm_name="pcef.realm")
    ocs = OCS(origin_host="ocs-0.ocs.realm", realm_name="ocs.realm")
    
    # Auto-create configuration from entities
    config = create_diameter_config_from_entities(pcef, ocs)
    print(f"Auto-created config: {config}")
    
    # Create service with auto config
    data_service = DataService(pcef=pcef, ocs=ocs, diameter_config=config)
    print(f"Created DataService with auto config")

def example_solution_style():
    """Example matching the solution.py style but with new DiameterConfig."""
    print("\n=== Solution Style with DiameterConfig ===")
    
    # Create PCEF
    pcef = PCEF(origin_host="pcef-0.pcef.realm", realm_name="pcef.realm")
    
    # Create DSC node
    dsc_node = Node(origin_host="dsc-0.dsc.realm", realm_name="dsc.realm", 
                   ip_addresses=["pcrf-server"], tcp_port=30001)
    
    # Setup peer connections
    pcef.add_node_as_peer(dsc_node)
    pcef.add_gx_realm("pcrf.realm")
    
    # Create explicit configuration for PCRF realm routing
    config = DiameterConfig()
    config.set_gx_routing(destination_realm="pcrf.realm")
    
    # Create service with explicit routing
    data_service = DataService(pcef=pcef, diameter_config=config)
    print(f"Created DataService with PCRF realm routing")
    
    # Now send_request will automatically route to pcrf.realm
    print("Service ready for message routing to pcrf.realm")

if __name__ == "__main__":
    example_manual_config()
    example_auto_config() 
    example_solution_style()
