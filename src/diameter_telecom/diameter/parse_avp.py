"""
Diameter AVP (Attribute-Value Pair) Parsing Utilities

This module provides functions for parsing and extracting information from
Diameter AVPs (Attribute-Value Pairs) in telecommunications messages. It includes
utilities for handling subscriber identification, IP addresses, charging rules,
QoS parameters, and other telecom-specific attributes.

The module is designed to work with the base diameter library's message structures
and provides telecom-specific parsing functionality.
"""

from typing import List, Tuple, Optional, Set, Dict
from diameter.message.constants import *
from diameter.message.avp.grouped import SubscriptionId
from .message import DiameterMessage

import logging
logger = logging.getLogger(__name__)

def parse_subscription_id(subscription_id: List[SubscriptionId]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Parse subscription ID AVPs to extract subscriber identifiers.
    
    This function extracts MSISDN, IMSI, and SIP URI from subscription ID AVPs.
    It handles multiple subscription ID types that may be present in a message.
    
    Args:
        subscription_id (List[SubscriptionId]): List of subscription ID AVPs
        
    Returns:
        Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]: Tuple containing
            (msisdn, imsi, sip_uri, nai, private). Each value may be None if not present.
            
    Example:
        >>> msisdn, imsi, sip_uri = parse_subscription_id(message.subscription_id)
    """
    msisdn = None
    imsi = None
    sip_uri = None
    nai = None
    private = None
    for i in subscription_id:
        if i.subscription_id_type == E_SUBSCRIPTION_ID_TYPE_END_USER_E164:
            msisdn = i.subscription_id_data
        elif i.subscription_id_type == E_SUBSCRIPTION_ID_TYPE_END_USER_IMSI:
            imsi = i.subscription_id_data
        elif i.subscription_id_type == E_SUBSCRIPTION_ID_TYPE_END_USER_SIP_URI:
            sip_uri = i.subscription_id_data
        elif i.subscription_id_type == E_SUBSCRIPTION_ID_TYPE_END_USER_NAI:
            nai = i.subscription_id_data
        elif i.subscription_id_type == E_SUBSCRIPTION_ID_TYPE_END_USER_PRIVATE:
            private = i.subscription_id_data
    return (msisdn, imsi, sip_uri, nai, private)

import socket
def decode_framed_ip_address(ip_bytes: bytes) -> Optional[str]:
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
        # Bounds checking to prevent list index out of range
        if not raw_bytes or len(raw_bytes) < 2:
            logger.warning(f"Invalid framed IPv6 prefix data - too short: {len(raw_bytes) if raw_bytes else 0} bytes")
            return None
            
        reserved_byte = raw_bytes[0]
        prefix_length = raw_bytes[1]
        ipv6_prefix_bytes = raw_bytes[2:]
        ipv6_prefix_bytes_padded = ipv6_prefix_bytes.ljust(16, b'\x00')
        ipv6_address = ipaddress.IPv6Address(ipv6_prefix_bytes_padded)
        return f"{ipv6_address}/{prefix_length}"
    except Exception as e:
        logger.error(f"Error decoding framed IPv6: {raw_bytes}, error: {e}")
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


def parse_user_location_info_fixed(hex_string: str):
    if isinstance(hex_string, bytes):
        hex_string = hex_string.hex()
    # Wireshark interprets the MNC using BCD digits in this order:
    #   - Digit 1: Byte 3 low nibble
    #   - Digit 2: Byte 3 high nibble
    #   - Digit 3: Byte 2 high nibble
    # This may differ from raw spec parsing (3GPP TS 24.008), but matches real-world tools.
    def decode_mcc_mnc(data):
        # Bounds checking to prevent list index out of range
        if not data or len(data) < 3:
            logger.warning(f"Invalid MCC/MNC data - too short: {len(data) if data else 0} bytes")
            return "000", "00"  # Return default values
            
        # MCC
        mcc = f"{data[0] & 0x0F}{(data[0] & 0xF0) >> 4}{data[1] & 0x0F}"

        # Wireshark-like MNC interpretation (b3 low, b3 high, b2 high)
        mnc_digit1 = data[2] & 0x0F
        mnc_digit2 = (data[2] & 0xF0) >> 4
        mnc_digit3 = (data[1] & 0xF0) >> 4

        if mnc_digit3 == 0xF:
            mnc = f"{mnc_digit1}{mnc_digit2}"
        else:
            mnc = f"{mnc_digit1}{mnc_digit2}{mnc_digit3}"

        return mcc, mnc

    try:
        data = bytes.fromhex(hex_string.replace(" ", ""))
        
        # Bounds checking for main data
        if not data or len(data) < 1:
            logger.warning(f"Invalid location info data - empty")
            return None
            
        if data[0] != 0x82:
            logger.warning(f"Unsupported Location Type: {data[0] if data else 'None'}")
            return None
            
        # Check if we have enough data for TAI part
        if len(data) < 6:
            logger.warning(f"Invalid location info data - too short for TAI: {len(data)} bytes")
            return None

        # --- TAI part (bytes 1–5) ---
        mcc_tai, mnc_tai = decode_mcc_mnc(data[1:4])
        tac = int.from_bytes(data[4:6], byteorder='big')

        # Check if we have enough data for ECGI part
        if len(data) < 13:
            logger.warning(f"Invalid location info data - too short for ECGI: {len(data)} bytes")
            return None

        # --- ECGI part (bytes 6–12) ---
        mcc_ecgi, mnc_ecgi = decode_mcc_mnc(data[6:9])
        eci = int.from_bytes(data[9:13], byteorder='big')  # 4 full bytes
    except Exception as e:
        logger.error(f"Error parsing location info: {e}")
        return None

    return {
        "TAI": {
            "MCC": mcc_tai,
            "MNC": mnc_tai,
            "TAC": tac
        },
        "ECGI": {
            "MCC": mcc_ecgi,
            "MNC": mnc_ecgi,
            "ECI": eci
        }
    }


def build_user_location_info_hex(parsed):
    def encode_mcc_mnc(mcc: str, mnc: str) -> bytes:
        # MCC: always 3 digits
        mcc_digit1 = int(mcc[0])
        mcc_digit2 = int(mcc[1])
        mcc_digit3 = int(mcc[2])

        # MNC: pad to 3 digits if needed
        mnc = mnc.zfill(3)
        mnc_digit1 = int(mnc[0])  # b3 low nibble
        mnc_digit2 = int(mnc[1])  # b3 high nibble
        mnc_digit3 = int(mnc[2])  # b2 high nibble

        byte1 = (mcc_digit2 << 4) | mcc_digit1
        byte2 = (mnc_digit3 << 4) | mcc_digit3
        byte3 = (mnc_digit2 << 4) | mnc_digit1

        return bytes([byte1, byte2, byte3])

    result = bytearray()
    result.append(0x82)  # fixed type byte

    # Encode TAI
    tai = parsed["TAI"]
    result += encode_mcc_mnc(tai["MCC"], tai["MNC"])
    result += tai["TAC"].to_bytes(2, byteorder='big')

    # Encode ECGI
    ecgi = parsed["ECGI"]
    result += encode_mcc_mnc(ecgi["MCC"], ecgi["MNC"])
    result += ecgi["ECI"].to_bytes(4, byteorder='big')

    return result.hex()

from diameter.message.avp.grouped import UsageMonitoringInformation
def parse_usage_monitoring_information(umi_list: List[UsageMonitoringInformation]) -> Dict[str, Dict[str, int]]:
    umi_gsu_usu: Dict[str, Dict[str, int]] = {}
    gsu: Dict[str, int] = {}
    usu: Dict[str, int] = {}
    for umi in umi_list:
        if umi.granted_service_unit and umi.granted_service_unit.cc_total_octets:
            if umi.granted_service_unit.cc_total_octets > 0:
                monitoring_key = umi.monitoring_key
                if isinstance(monitoring_key, bytes):
                    monitoring_key = monitoring_key.decode('utf-8')
                gsu[monitoring_key] = umi.granted_service_unit.cc_total_octets
            else:
                gsu[monitoring_key] = 0
        if umi.used_service_unit and umi.used_service_unit.cc_total_octets:
            if umi.used_service_unit.cc_total_octets > 0:
                monitoring_key = umi.monitoring_key
                if isinstance(monitoring_key, bytes):
                    monitoring_key = monitoring_key.decode('utf-8')
                usu[monitoring_key] = umi.used_service_unit.cc_total_octets
            else:
                usu[monitoring_key] = 0
    if gsu:
        umi_gsu_usu['granted_service_unit'] = gsu
    if usu:
        umi_gsu_usu['used_service_unit'] = usu
    return umi_gsu_usu
    



__all__ = [
    'parse_subscription_id',
    'decode_framed_ip_address',
    'decode_framed_ipv6',
    'check_charging_rule_remove',
    'check_charging_rule_install',
    'check_qos',
    'check_event_trigger',
    'check_rat_type',
    'parse_user_location_info_fixed',
    'build_user_location_info_hex',
    'parse_usage_monitoring_information'
] 