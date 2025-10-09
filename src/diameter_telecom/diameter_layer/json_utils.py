import json
from typing import Any, Dict, List, Union
from diameter.message import Message
from diameter.message.avp import Avp, AvpGrouped
from .parse_avp import (
    decode_framed_ip_address,
    decode_framed_ipv6,
    parse_user_location_info_fixed
)

__all__ = [
    "message_to_json",
    "message_to_compact_json",
    "message_to_class_json",
    "avp_to_json",
    "avp_to_compact_json"
]

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
    return _avp_to_dict(avp)


def avp_to_compact_json(avp: Avp) -> Dict[str, Any]:
    return _compact_avp_from_avp(avp)


def message_to_class_json(message: Message) -> Dict[str, Any]:
    """Convert any Diameter message to JSON that mirrors class structure."""
    result = {
        "message_type": message.name,
        "header": {
            "version": message.header.version,
            "length": message.header.length,
            "flags": {
                "request": message.header.is_request,
                "proxyable": message.header.is_proxyable,
                "error": message.header.is_error,
                "retransmit": message.header.is_retransmit
            },
            "command_code": message.header.command_code,
            "application_id": message.header.application_id,
            "hop_by_hop_identifier": message.header.hop_by_hop_identifier,
            "end_to_end_identifier": message.header.end_to_end_identifier
        },
        "avps": {},
        "avps_not_set": []
    }
    
    # Group AVPs by name to handle multiple occurrences
    avp_groups = {}
    for avp in message.avps:
        if avp.name not in avp_groups:
            avp_groups[avp.name] = []
        avp_groups[avp.name].append(avp)
    
    # Process each AVP group
    for avp_name, avp_list in avp_groups.items():
        field_name = _avp_name_to_field_name(avp_name)
        
        if len(avp_list) == 1:
            # Single AVP
            avp = avp_list[0]
            result["avps"][field_name] = _process_single_avp(avp)
        else:
            # Multiple AVPs with same name
            result["avps"][field_name] = [_process_single_avp(avp) for avp in avp_list]
    
    # Add common AVPs that are not set
    result["avps_not_set"] = _get_common_avps_not_set(avp_groups.keys())
    
    return result


def _avp_name_to_field_name(avp_name: str) -> str:
    """Convert AVP name to Python field name (snake_case)."""
    # Handle special cases and common patterns
    field_name = avp_name.lower()
    field_name = field_name.replace('-', '_')
    field_name = field_name.replace('3gpp_', '3gpp_')
    field_name = field_name.replace('cc_', 'cc_')
    field_name = field_name.replace('_id', '_id')
    return field_name


def _process_single_avp(avp: Avp) -> Any:
    """Process a single AVP and return its structured value."""
    if isinstance(avp, AvpGrouped):
        # Handle grouped AVPs
        grouped_result = {}
        for sub_avp in avp.value:
            sub_field_name = _avp_name_to_field_name(sub_avp.name)
            grouped_result[sub_field_name] = _process_single_avp(sub_avp)
        return grouped_result
    else:
        # Handle simple AVPs
        value = avp.value
        
        # Convert bytes to readable format
        if isinstance(value, bytes):
            return _convert_byte_value(avp.name, value)
        elif isinstance(value, (str, int, float, bool)) or value is None:
            return value
        elif isinstance(value, list):
            return value
        else:
            return str(value)


def _get_common_avps_not_set(present_avps):
    """Get list of common AVPs that are not present in the message."""
    # Common AVPs that might be expected in Diameter messages
    common_avps = [
        "Destination-Host",
        "User-Name", 
        "CC-Sub-Session-Id",
        "Acct-Multi-Session-Id",
        "Event-Timestamp",
        "Service-Identifier",
        "Termination-Cause",
        "Requested-Service-Unit",
        "Requested-Action",
        "Used-Service-Unit",
        "Multiple-Services-Indicator",
        "Multiple-Services-Credit-Control",
        "Service-Parameter-Info",
        "CC-Correlation-Id",
        "User-Equipment-Info-Extension",
        "Proxy-Info",
        "Proxy-Host",
        "Proxy-State",
        "Failed-AVP",
        "Experimental-Result",
        "Experimental-Result-Code",
        "Experimental-Result-Vendor-Id",
        "Vendor-Specific-Application-Id",
        "Redirect-Host",
        "Redirect-Host-Usage",
        "Redirect-Max-Cache-Time",
        "E2E-Sequence",
        "AVP"
    ]
    
    # Return AVPs that are not present
    return [avp for avp in common_avps if avp not in present_avps]


if __name__ == "__main__":
    from ..message import DiameterMessage
    ccr_i = DiameterMessage("01000398c000011001000016bd1fb085100edcd2000001074000005064302d6774747665706330312e63656c6c696e6b67792e636f6d3b313732383133363936353b3337343636363233343b36373031343730352d373338303032303032363035303031000001024000000c01000016000001084000002264302d6774747665706330312e63656c6c696e6b67792e636f6d0000000001284000001563656c6c696e6b67792e636f6d0000000000011b4000002e616f702e646174612e6d6e633030322e6d63633733382e336770706e6574776f726b2e6f72670000000001a04000000c000000010000019f4000000c000000000000042480000010000000c10003000100000017c000000e000028af69000000000001164000000c00000002000001bb40000028000001c24000000c00000000000001bc40000012353932373538393930330000000001bb4000002c000001c24000000c00000001000001bc4000001737333830303230303236303530303100000000084000000c0a00901500000403c0000010000028af000000050000040880000010000028af000003e8000001ca4000002c000001cb0000000c00000000000001cc0000001833353332323031303031303734373139000003f8c000002c000028af0000041080000010000028af02dc6c000000041180000010000028af0083d6000000041980000058000028af00000404c0000010000028af000000080000040a8000003c000028af0000041680000010000028af000000030000041780000010000028af000000010000041880000010000028af0000000100000012c0000012000028af373338303032000000000006c0000010000028afbe500c3100000016c0000014000028af01372800003c75490000001e4000001a746573742e63656c6c696e6b67792e636f6d0000000003e8c0000010000028af00000000000001f5c0000012000028af0001be500c090000000003fec0000024000028af000001f7c0000016000028af3234313232373436383200000000038dc0000018000028af3733383030326666666566660000027480000038000028af0000010a4000000c000028af0000027580000010000028af000000010000027680000010000028afa22188030000027480000038000028af0000010a4000000c000028af0000027580000010000028af000000020000027680000010000028af000000b00000011a4000002264302d6774747665706330312e63656c6c696e6b67792e636f6d0000")
    # print(ccr_i.to_dict())
    print(message_to_json(ccr_i.message))