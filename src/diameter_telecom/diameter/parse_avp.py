"""
Diameter AVP (Attribute-Value Pair) Parsing Utilities

This module provides functions for parsing and extracting information from
Diameter AVPs (Attribute-Value Pairs) in telecommunications messages. It includes
utilities for handling subscriber identification, IP addresses, charging rules,
QoS parameters, and other telecom-specific attributes.

The module is designed to work with the base diameter library's message structures
and provides telecom-specific parsing functionality.
"""

from typing import List, Tuple, Optional, Set
from diameter.message.constants import *
from diameter.message.avp.grouped import SubscriptionId
from .message import DiameterMessage

import logging
logger = logging.getLogger(__name__)

def parse_subscription_id(subscription_id: List[SubscriptionId]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Parse subscription ID AVPs to extract subscriber identifiers.
    
    This function extracts MSISDN, IMSI, and SIP URI from subscription ID AVPs.
    It handles multiple subscription ID types that may be present in a message.
    
    Args:
        subscription_id (List[SubscriptionId]): List of subscription ID AVPs
        
    Returns:
        Tuple[Optional[str], Optional[str], Optional[str]]: Tuple containing
            (msisdn, imsi, sip_uri). Each value may be None if not present.
            
    Example:
        >>> msisdn, imsi, sip_uri = parse_subscription_id(message.subscription_id)
    """
    msisdn = None
    imsi = None
    sip_uri = None
    for i in subscription_id:
        if i.subscription_id_type == E_SUBSCRIPTION_ID_TYPE_END_USER_E164:
            msisdn = i.subscription_id_data
        elif i.subscription_id_type == E_SUBSCRIPTION_ID_TYPE_END_USER_IMSI:
            imsi = i.subscription_id_data
        elif i.subscription_id_type == E_SUBSCRIPTION_ID_TYPE_END_USER_SIP_URI:
            sip_uri = i.subscription_id_data
    return (msisdn, imsi, sip_uri)

import socket
def bytes_to_ip(ip_bytes: bytes) -> Optional[str]:
    """
    Convert IP address bytes to string representation.
    
    Args:
        ip_bytes (bytes): IP address in bytes format
        
    Returns:
        Optional[str]: IP address string or None if conversion fails
        
    Example:
        >>> ip = bytes_to_ip(b'\\xc0\\xa8\\x01\\x01')
        >>> print(ip)
        '192.168.1.1'
    """
    try:
        return socket.inet_ntoa(ip_bytes)
    except:
        logger.error(f"Error converting bytes to IP: {ip_bytes}")
        return None
    
import ipaddress
def decode_framed_ipv6(raw_bytes: bytes) -> Optional[str]:
    """
    Decode framed IPv6 prefix from raw bytes.
    
    This function decodes the framed IPv6 prefix AVP format, which includes
    a reserved byte, prefix length, and IPv6 prefix.
    
    Args:
        raw_bytes (bytes): Raw bytes containing the framed IPv6 prefix
        
    Returns:
        Optional[str]: IPv6 prefix in CIDR notation or None if decoding fails
        
    Example:
        >>> prefix = decode_framed_ipv6(b'\\x00\\x40\\x20\\x01\\x0d\\xb8')
        >>> print(prefix)
        '2001:db8::/64'
    """
    try:
        reserved_byte = raw_bytes[0]
        prefix_length = raw_bytes[1]
        ipv6_prefix_bytes = raw_bytes[2:]
        ipv6_prefix_bytes_padded = ipv6_prefix_bytes.ljust(16, b'\x00')
        ipv6_address = ipaddress.IPv6Address(ipv6_prefix_bytes_padded)
        return f"{ipv6_address}/{prefix_length}"
    except:
        logger.error(f"Error decoding framed IPv6: {raw_bytes}")
        return None
    

def check_charging_rule_remove(diameter_message: DiameterMessage) -> Optional[Set[str]]:
    """
    Extract charging rules to be removed from a Diameter message.
    
    This function parses the charging-rule-remove AVP to extract the names of
    charging rules that should be removed. It handles both rule names and
    rule base names.
    
    Args:
        diameter_message (DiameterMessage): The Diameter message to parse
        
    Returns:
        Optional[Set[str]]: Set of charging rule names to remove, or None if parsing fails
        
    Example:
        >>> rules = check_charging_rule_remove(message)
        >>> print(rules)
        {'rule1', 'rule2'}
    """
    message = diameter_message.message
    pcc_rules = set()
    try:
        if hasattr(message, "charging_rule_remove") and message.charging_rule_remove:
            for i in message.charging_rule_remove:
                if i.charging_rule_base_name:
                    for j in i.charging_rule_base_name:
                        pcc_rules.add(j)
                if i.charging_rule_name:
                    for j in i.charging_rule_name:
                        pcc_rules.add(j)
                if i.charging_rule_definition:
                    for j in i.charging_rule_definition:
                        charging_rule_name = j.charging_rule_name
                        pcc_rules.add(charging_rule_name)
            return pcc_rules
    except Exception as e:
        logger.error(f"Error then trying to remove pcc_rules from GxSession: {e}. This error is not relevant to the flow")

def check_charging_rule_install(diameter_message: DiameterMessage) -> Optional[Set[str]]:
    """
    Extract charging rules to be installed from a Diameter message.
    
    This function parses the charging-rule-install AVP to extract the names of
    charging rules that should be installed. It handles both rule names and
    rule base names.
    
    Args:
        diameter_message (DiameterMessage): The Diameter message to parse
        
    Returns:
        Optional[Set[str]]: Set of charging rule names to install, or None if parsing fails
        
    Example:
        >>> rules = check_charging_rule_install(message)
        >>> print(rules)
        {'rule1', 'rule2'}
    """
    message = diameter_message.message
    pcc_rules = set()
    try:
        if hasattr(message, "charging_rule_install") and message.charging_rule_install:
            for i in message.charging_rule_install:
                if i.charging_rule_base_name:
                    for j in i.charging_rule_base_name:
                        pcc_rules.add(j)
                if i.charging_rule_name:
                    for j in i.charging_rule_name:
                        pcc_rules.add(j)
                if i.charging_rule_definition:
                    for j in i.charging_rule_definition:
                        charging_rule_name = j.charging_rule_name
                        pcc_rules.add(charging_rule_name)
            return pcc_rules
    except Exception as e:
        logger.error(f"Error then trying to add pcc_rules from GxSession: {e}. This error is not relevant to the flow")


def check_qos(diameter_message: DiameterMessage) -> Optional[Tuple[int, int]]:
    """
    Extract QoS parameters from a Diameter message.
    
    This function parses the default-eps-bearer-qos AVP to extract QoS class
    identifier and priority level.
    
    Args:
        diameter_message (DiameterMessage): The Diameter message to parse
        
    Returns:
        Optional[Tuple[int, int]]: Tuple of (qos_class_identifier, priority_level)
            or None if parsing fails
        
    Example:
        >>> qos_params = check_qos(message)
        >>> if qos_params:
        ...     qci, priority = qos_params
        ...     print(f"QCI: {qci}, Priority: {priority}")
    """
    message = diameter_message.message
    try:
        if hasattr(message, "default_eps_bearer_qos") and message.default_eps_bearer_qos:
                default_eps_bearer_qos = message.default_eps_bearer_qos
                qos_class_identifier = default_eps_bearer_qos.qos_class_identifier
                arp = default_eps_bearer_qos.allocation_retention_priority
                priority_level = arp.priority_level
                return qos_class_identifier, priority_level
    except:
        logger.error(f"Error then trying to set QoS attributes from GxSession")
        pass

def check_event_trigger(diameter_message: DiameterMessage) -> Optional[List[int]]:
    """
    Extract event triggers from a Diameter message.
    
    This function parses the event-trigger AVP to extract the list of
    event triggers that should be monitored.
    
    Args:
        diameter_message (DiameterMessage): The Diameter message to parse
        
    Returns:
        Optional[List[int]]: List of event trigger values or None if parsing fails
        
    Example:
        >>> triggers = check_event_trigger(message)
        >>> if triggers:
        ...     print(f"Event triggers: {triggers}")
    """
    message = diameter_message.message
    event_trigger = []
    try:
        if hasattr(message, "event_trigger") and message.event_trigger:
            for i in message.event_trigger:
                event_trigger.append(i)
            return event_trigger
    except:
        logger.error(f"Error then trying to set Event Trigger from GxSession")
        pass

def check_rat_type(diameter_message: DiameterMessage) -> Optional[int]:
    """
    Extract RAT (Radio Access Technology) type from a Diameter message.
    
    This function parses the rat-type AVP to extract the type of radio
    access technology being used.
    
    Args:
        diameter_message (DiameterMessage): The Diameter message to parse
        
    Returns:
        Optional[int]: RAT type value or None if parsing fails
        
    Example:
        >>> rat_type = check_rat_type(message)
        >>> if rat_type:
        ...     print(f"RAT Type: {rat_type}")
    """
    message = diameter_message.message
    try:
        if hasattr(message, "rat_type") and message.rat_type:
            return message.rat_type
    except:
        logger.error(f"Error then trying to set RAT Type from GxSession")
        pass


