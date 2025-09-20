import json
from typing import Any, Dict, List, Union
from diameter.message import Message
from diameter.message.avp import Avp, AvpGrouped
from .parse_avp import (
    decode_framed_ip_address,
    decode_framed_ipv6,
    parse_user_location_info_fixed
)


def _convert_byte_value(avp_name: str, value: Any) -> Any:
    """Convert byte values to more readable formats based on AVP type."""
    if not isinstance(value, bytes):
        return value
    
    # Handle specific AVP types that have known byte formats
    if avp_name in ['Framed-IP-Address', '3GPP-SGSN-Address']:
        # Try to decode as IPv4 address
        if len(value) == 4:
            ipv4 = decode_framed_ip_address(value)
            if ipv4:
                return f"{ipv4} ({value.hex()})"
    
    elif avp_name == 'Framed-IPv6-Prefix':
        # Try to decode as IPv6 prefix
        ipv6 = decode_framed_ipv6(value)
        if ipv6:
            return f"{ipv6} ({value.hex()})"
    
    elif avp_name == '3GPP-User-Location-Info':
        # Parse user location info
        try:
            location_info = parse_user_location_info_fixed(value.hex())
            if location_info:
                return {
                    "parsed": location_info,
                    "raw": value.hex()
                }
        except:
            pass
    
    # For other byte values, try UTF-8 decode first, then fall back to hex
    try:
        decoded = value.decode('utf-8')
        if decoded.isprintable():
            return f"{decoded} ({value.hex()})"
    except:
        pass
    
    # Fall back to hex representation
    return f"b'{value.hex()}'"


def message_to_json(message: Message) -> Dict[str, Any]:
    """Convert a Diameter Message to JSON format.
    
    Converts a Message object to a JSON-serializable dictionary that captures
    all the information shown in the print format, including message header
    details and all AVPs with their properties.
    
    Args:
        message: A Diameter Message object to convert
        
    Returns:
        A dictionary containing the message structure in JSON format
    """
    return {
        "message": {
            "name": message.name,
            "header": _header_to_dict(message.header),
            "avps": [_avp_to_dict(avp) for avp in message.avps]
        }
    }


def _header_to_dict(header) -> Dict[str, Any]:
    """Convert MessageHeader to dictionary format."""
    return {
        "version": header.version,
        "length": header.length,
        "flags": {
            "request": header.is_request,
            "proxyable": header.is_proxyable,
            "error": header.is_error,
            "retransmit": header.is_retransmit
        },
        "command_code": header.command_code,
        "application_id": header.application_id,
        "hop_by_hop_identifier": header.hop_by_hop_identifier,
        "end_to_end_identifier": header.end_to_end_identifier
    }


def _avp_to_dict(avp: Avp) -> Dict[str, Any]:
    """Convert an AVP to dictionary format, handling grouped AVPs recursively."""
    result = {
        "name": avp.name,
        "code": avp.code,
        "flags": {
            "vendor": avp.is_vendor,
            "mandatory": avp.is_mandatory,
            "private": avp.is_private
        },
        "length": avp.length,
        "vendor_id": avp.vendor_id
    }
    
    # Handle grouped AVPs recursively
    if isinstance(avp, AvpGrouped):
        result["value"] = [_avp_to_dict(sub_avp) for sub_avp in avp.value]
    else:
        # Handle different value types appropriately
        value = avp.value
        if isinstance(value, (str, int, float, bool)) or value is None:
            result["value"] = value
        elif isinstance(value, list):
            result["value"] = value
        else:
            # Convert byte values to readable format
            result["value"] = _convert_byte_value(avp.name, value)
    
    return result


def message_to_compact_json(message_or_dict: Union[Message, Dict[str, Any]]) -> Dict[str, Any]:
    """Convert a Diameter Message or JSON dict to a compact JSON format for analysis.
    
    Removes less relevant fields like length, AVP flags, and vendor_id to focus
    on the essential data for analysis.
    
    Args:
        message_or_dict: A Diameter Message object or JSON dictionary to convert
        
    Returns:
        A compact dictionary containing the essential message structure
    """
    if isinstance(message_or_dict, dict):
        # Handle dictionary input (from previous message_to_json call)
        message_data = message_or_dict["message"]
        return {
            "message": {
                "name": message_data["name"],
                "header": {
                    "version": message_data["header"]["version"],
                    "flags": message_data["header"]["flags"],
                    "command_code": message_data["header"]["command_code"],
                    "application_id": message_data["header"]["application_id"],
                    "hop_by_hop_identifier": message_data["header"]["hop_by_hop_identifier"],
                    "end_to_end_identifier": message_data["header"]["end_to_end_identifier"]
                },
                "avps": [_compact_avp_from_dict(avp) for avp in message_data["avps"]]
            }
        }
    else:
        # Handle Message object input
        return {
            "message": {
                "name": message_or_dict.name,
                "header": {
                    "version": message_or_dict.header.version,
                    "flags": {
                        "request": message_or_dict.header.is_request,
                        "proxyable": message_or_dict.header.is_proxyable,
                        "error": message_or_dict.header.is_error,
                        "retransmit": message_or_dict.header.is_retransmit
                    },
                    "command_code": message_or_dict.header.command_code,
                    "application_id": message_or_dict.header.application_id,
                    "hop_by_hop_identifier": message_or_dict.header.hop_by_hop_identifier,
                    "end_to_end_identifier": message_or_dict.header.end_to_end_identifier
                },
                "avps": [_compact_avp_from_avp(avp) for avp in message_or_dict.avps]
            }
        }


def _compact_avp_from_avp(avp: Avp) -> Dict[str, Any]:
    """Convert AVP object to compact format."""
    result = {
        "name": avp.name,
        # "code": avp.code
    }
    
    # Add vendor_id only if it's not zero
    if avp.vendor_id:
        result["vendor_id"] = avp.vendor_id
    
    # Handle grouped AVPs recursively
    if isinstance(avp, AvpGrouped):
        result["value"] = [_compact_avp_from_avp(sub_avp) for sub_avp in avp.value]
    else:
        # Handle different value types appropriately
        value = avp.value
        if isinstance(value, (str, int, float, bool)) or value is None:
            result["value"] = value
        elif isinstance(value, list):
            result["value"] = value
        else:
            # Convert byte values to readable format
            result["value"] = _convert_byte_value(avp.name, value)
    
    return result


def _compact_avp_from_dict(avp_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Convert AVP dictionary to compact format."""
    result = {
        "name": avp_dict["name"],
        # "code": avp_dict["code"]
    }
    
    # Add vendor_id only if it exists and is not zero
    if "vendor_id" in avp_dict and avp_dict["vendor_id"]:
        result["vendor_id"] = avp_dict["vendor_id"]
    
    # Handle grouped AVPs recursively
    if isinstance(avp_dict["value"], list) and avp_dict["value"] and isinstance(avp_dict["value"][0], dict):
        result["value"] = [_compact_avp_from_dict(sub_avp) for sub_avp in avp_dict["value"]]
    else:
        # Convert byte values to readable format if they're still in byte format
        value = avp_dict["value"]
        if isinstance(value, str) and value.startswith("b'") and value.endswith("'"):
            # This is a string representation of bytes, try to convert back to bytes for parsing
            try:
                hex_part = value[2:-1]  # Remove b' and '
                byte_value = bytes.fromhex(hex_part)
                result["value"] = _convert_byte_value(avp_dict["name"], byte_value)
            except:
                result["value"] = value
        else:
            result["value"] = value
    
    return result


def avp_to_json(avp: Avp) -> Dict[str, Any]:
    """Convert a single AVP to JSON format.
    
    Converts an AVP object to a JSON-serializable dictionary with all its
    properties and converted byte values.
    
    Args:
        avp: An AVP object to convert
        
    Returns:
        A dictionary containing the AVP structure in JSON format
    """
    return _avp_to_dict(avp)


def avp_to_compact_json(avp: Avp) -> Dict[str, Any]:
    """Convert a single AVP to compact JSON format.
    
    Converts an AVP object to a compact JSON-serializable dictionary,
    removing less relevant fields like length and flags.
    
    Args:
        avp: An AVP object to convert
        
    Returns:
        A compact dictionary containing the AVP structure
    """
    return _compact_avp_from_avp(avp)