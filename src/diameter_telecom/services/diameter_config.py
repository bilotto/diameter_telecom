#!/usr/bin/env python3
"""
DiameterConfig - Explicit configuration for Diameter Services.
Makes service configuration more intuitive and less error-prone.
"""

from typing import Dict, Optional, Any
from collections import UserDict
from ..diameter.constants import APP_3GPP_GX, APP_3GPP_RX, APP_3GPP_SY
import logging

logger = logging.getLogger(__name__)

def _normalize_keys_to_int(config: Dict[Any, Any]) -> Dict[int, Any]:
    normalized: Dict[int, Any] = {}
    for key, value in (config or {}).items():
        try:
            normalized[int(key)] = value
        except Exception:
            # Keep as-is if not convertible; maintains maximal compatibility
            normalized[key] = value
    return normalized


class DiameterConfig(UserDict):
    """
    Explicit configuration for Diameter Services with full backward compatibility.
    Subclasses UserDict so existing dict-based code keeps working:
    - Access via config[app_id]['destination_realm']
    - Iteration and other dict operations
    Also adds helpers like set_gx_routing(), set_rx_routing(), set_sy_routing().
    """

    def __init__(self, initial: Optional[Dict[int, Dict[str, Any]]] = None):
        base = {
            APP_3GPP_GX: {},
            APP_3GPP_RX: {},
            APP_3GPP_SY: {},
        }
        if initial:
            base.update(_normalize_keys_to_int(initial))
        super().__init__(base)
    
    def set_gx_routing(self, origin_realm: str = None, destination_realm: str = None, destination_host: str = None):
        """Configure Gx application routing."""
        self.data[APP_3GPP_GX] = {
            'origin_realm': origin_realm,
            'destination_realm': destination_realm,
            'destination_host': destination_host
        }
        logger.debug(f"Gx routing configured: {self.data[APP_3GPP_GX]}")
    
    def set_rx_routing(self, origin_realm: str = None, destination_realm: str = None, destination_host: str = None):
        """Configure Rx application routing."""
        self.data[APP_3GPP_RX] = {
            'origin_realm': origin_realm,
            'destination_realm': destination_realm,
            'destination_host': destination_host
        }
        logger.debug(f"Rx routing configured: {self.data[APP_3GPP_RX]}")
    
    def set_sy_routing(self, origin_realm: str = None, destination_realm: str = None, destination_host: str = None):
        """Configure Sy application routing."""
        self.data[APP_3GPP_SY] = {
            'origin_realm': origin_realm,
            'destination_realm': destination_realm,
            'destination_host': destination_host
        }
        logger.debug(f"Sy routing configured: {self.data[APP_3GPP_SY]}")
    
    def get_config(self) -> Dict[int, Dict[str, str]]:
        """Get the internal configuration dictionary (for legacy callers)."""
        return self.data
    
    def get_app_config(self, app_id: int) -> Dict[str, str]:
        """Get configuration for a specific application."""
        return self.data.get(app_id, {})
    
    def __str__(self):
        """String representation for debugging."""
        return f"DiameterConfig({self.data})"
    
    def __repr__(self):
        return self.__str__()

def create_diameter_config_from_entities(pcef, ocs=None, af=None):
    """
    Auto-create DiameterConfig from 3GPP entities.
    Extracts realm information from entities and creates appropriate routing.
    """
    config = DiameterConfig()
    
    # Gx routing (always present with PCEF)
    if pcef:
        config.set_gx_routing(
            origin_realm=pcef.realm_name,
            destination_realm=pcef.realm_name  # Default to same realm
        )
        logger.info(f"Auto-configured Gx routing for PCEF {pcef.origin_host}")
    
    # Sy routing (if OCS present)
    if ocs:
        config.set_sy_routing(
            origin_realm=ocs.realm_name,
            destination_realm=ocs.realm_name
        )
        logger.info(f"Auto-configured Sy routing for OCS {ocs.origin_host}")
    
    # Rx routing (if AF present)
    if af:
        config.set_rx_routing(
            origin_realm=af.realm_name,
            destination_realm=af.realm_name
        )
        logger.info(f"Auto-configured Rx routing for AF {af.origin_host}")
    
    return config
