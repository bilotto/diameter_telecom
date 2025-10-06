from diameter_telecom.diameter.message import DiameterMessage
from diameter_telecom.diameter.json_utils import *
ccr_i = DiameterMessage("01000398c000011001000016bd1fb085100edcd2000001074000005064302d6774747665706330312e63656c6c696e6b67792e636f6d3b313732383133363936353b3337343636363233343b36373031343730352d373338303032303032363035303031000001024000000c01000016000001084000002264302d6774747665706330312e63656c6c696e6b67792e636f6d0000000001284000001563656c6c696e6b67792e636f6d0000000000011b4000002e616f702e646174612e6d6e633030322e6d63633733382e336770706e6574776f726b2e6f72670000000001a04000000c000000010000019f4000000c000000000000042480000010000000c10003000100000017c000000e000028af69000000000001164000000c00000002000001bb40000028000001c24000000c00000000000001bc40000012353932373538393930330000000001bb4000002c000001c24000000c00000001000001bc4000001737333830303230303236303530303100000000084000000c0a00901500000403c0000010000028af000000050000040880000010000028af000003e8000001ca4000002c000001cb0000000c00000000000001cc0000001833353332323031303031303734373139000003f8c000002c000028af0000041080000010000028af02dc6c000000041180000010000028af0083d6000000041980000058000028af00000404c0000010000028af000000080000040a8000003c000028af0000041680000010000028af000000030000041780000010000028af000000010000041880000010000028af0000000100000012c0000012000028af373338303032000000000006c0000010000028afbe500c3100000016c0000014000028af01372800003c75490000001e4000001a746573742e63656c6c696e6b67792e636f6d0000000003e8c0000010000028af00000000000001f5c0000012000028af0001be500c090000000003fec0000024000028af000001f7c0000016000028af3234313232373436383200000000038dc0000018000028af3733383030326666666566660000027480000038000028af0000010a4000000c000028af0000027580000010000028af000000010000027680000010000028afa22188030000027480000038000028af0000010a4000000c000028af0000027580000010000028af000000020000027680000010000028af000000b00000011a4000002264302d6774747665706330312e63656c6c696e6b67792e636f6d0000")

from diameter.message.commands import CreditControlRequest

import sys

import pprint

def pretty_display(value):
    if value is not None:
        pprint.pprint(value)

sys.displayhook = pretty_display

print(ccr_i.dump())

# >>> print(ccr_i.dump())
# Credit-Control <Version: 0x01, Length: 920, Flags: 0xc0 (request, proxyable), Hop-by-Hop Identifier: 0xbd1fb085, End-to-End Identifier: 0x100edcd2>
#   Session-Id <Code: 0x107, Flags: 0x40 (-M-), Length: 80, Val: d0-gttvepc01.cellinkgy.com;1728136965;374666234;67014705-738002002605001>
#   Origin-Host <Code: 0x108, Flags: 0x00 (---), Length: 34, Val: b'd0-gttvepc01.cellinkgy.com'>
#   Origin-Realm <Code: 0x128, Flags: 0x00 (---), Length: 21, Val: b'cellinkgy.com'>
#   Destination-Realm <Code: 0x11b, Flags: 0x40 (-M-), Length: 46, Val: b'aop.data.mnc002.mcc738.3gppnetwork.org'>
#   Auth-Application-Id <Code: 0x102, Flags: 0x40 (-M-), Length: 12, Val: 16777238>
#   CC-Request-Type <Code: 0x1a0, Flags: 0x40 (-M-), Length: 12, Val: 1>
#   CC-Request-Number <Code: 0x19f, Flags: 0x40 (-M-), Length: 12, Val: 0>
#   Origin-State-Id <Code: 0x116, Flags: 0x40 (-M-), Length: 12, Val: 2>
#   Subscription-Id <Code: 0x1bb, Flags: 0x40 (-M-), Length: 40>
#     Subscription-Id-Type <Code: 0x1c2, Flags: 0x40 (-M-), Length: 12, Val: 0>
#     Subscription-Id-Data <Code: 0x1bc, Flags: 0x40 (-M-), Length: 18, Val: 5927589903>
#   Subscription-Id <Code: 0x1bb, Flags: 0x40 (-M-), Length: 44>
#     Subscription-Id-Type <Code: 0x1c2, Flags: 0x40 (-M-), Length: 12, Val: 1>
#     Subscription-Id-Data <Code: 0x1bc, Flags: 0x40 (-M-), Length: 23, Val: 738002002605001>
#   User-Equipment-Info <Code: 0x1ca, Flags: 0x40 (-M-), Length: 44>
#     User-Equipment-Info-Type <Code: 0x1cb, Flags: 0x40 (-M-), Length: 12, Val: 0>
#     User-Equipment-Info-Value <Code: 0x1cc, Flags: 0x40 (-M-), Length: 24, Val: b'3532201001074719'>
#   Route-Record <Code: 0x11a, Flags: 0x40 (-M-), Length: 34, Val: b'd0-gttvepc01.cellinkgy.com'>
#   Supported-Features <Code: 0x274, Flags: 0xc0 (VM-), Length: 56, Vnd: TGPP>
#     Vendor-Id <Code: 0x10a, Flags: 0x40 (-M-), Length: 12, Val: 10415>
#     Feature-List-ID <Code: 0x275, Flags: 0xc0 (VM-), Length: 16, Vnd: TGPP, Val: 2>
#     Feature-List <Code: 0x276, Flags: 0xc0 (VM-), Length: 16, Vnd: TGPP, Val: 176>
#   QoS-Information <Code: 0x3f8, Flags: 0xc0 (VM-), Length: 44, Vnd: TGPP>
#     APN-Aggregate-Max-Bitrate-UL <Code: 0x411, Flags: 0xc0 (VM-), Length: 16, Vnd: TGPP, Val: 8640000>
#     APN-Aggregate-Max-Bitrate-DL <Code: 0x410, Flags: 0xc0 (VM-), Length: 16, Vnd: TGPP, Val: 48000000>
#   Framed-IP-Address <Code: 0x08, Flags: 0x40 (-M-), Length: 12, Val: b'\n\x00\x90\x15'>
#   IP-CAN-Type <Code: 0x403, Flags: 0xc0 (VM-), Length: 16, Vnd: TGPP, Val: 5>
#   RAT-Type <Code: 0x408, Flags: 0xc0 (VM-), Length: 16, Vnd: TGPP, Val: 1000>
#   3GPP-SGSN-MCC-MNC <Code: 0x12, Flags: 0xc0 (VM-), Length: 18, Vnd: TGPP, Val: 738002>
#   Called-Station-Id <Code: 0x1e, Flags: 0x40 (-M-), Length: 26, Val: test.cellinkgy.com>
#   Default-EPS-Bearer-QoS <Code: 0x419, Flags: 0xc0 (VM-), Length: 88, Vnd: TGPP>
#     QoS-Class-Identifier <Code: 0x404, Flags: 0xc0 (VM-), Length: 16, Vnd: TGPP, Val: 8>
#     Allocation-Retention-Priority <Code: 0x40a, Flags: 0xc0 (VM-), Length: 60, Vnd: TGPP>
#       Priority-Level <Code: 0x416, Flags: 0xc0 (VM-), Length: 16, Vnd: TGPP, Val: 3>
#       Pre-emption-Vulnerability <Code: 0x418, Flags: 0xc0 (VM-), Length: 16, Vnd: TGPP, Val: 1>
#       Pre-emption-Capability <Code: 0x417, Flags: 0xc0 (VM-), Length: 16, Vnd: TGPP, Val: 1>
#   3GPP-User-Location-Info <Code: 0x16, Flags: 0xc0 (VM-), Length: 20, Vnd: TGPP, Val: b'\x017(\x00\x00<uI'>
#   3GPP-MS-TimeZone <Code: 0x17, Flags: 0xc0 (VM-), Length: 14, Vnd: TGPP, Val: b'i\x00'>
#   Bearer-Usage <Code: 0x3e8, Flags: 0xc0 (VM-), Length: 16, Vnd: TGPP, Val: 0>
#   Access-Network-Charging-Address <Code: 0x1f5, Flags: 0x80 (V--), Length: 18, Vnd: TGPP, Val: (1, '190.80.12.9')>
#   Access-Network-Charging-Identifier-Gx <Code: 0x3fe, Flags: 0xc0 (VM-), Length: 36, Vnd: TGPP>
#     Access-Network-Charging-Identifier-Value <Code: 0x1f7, Flags: 0xc0 (VM-), Length: 22, Vnd: TGPP, Val: b'2412274682'>
#   Gx-Capability-List <Code: 0x424, Flags: 0x80 (V--), Length: 16, Vnd: Ericsson, Val: 196609>
#   3GPP-SGSN-Address <Code: 0x06, Flags: 0xc0 (VM-), Length: 16, Vnd: TGPP, Val: b'\xbeP\x0c1'>
#   RAI <Code: 0x38d, Flags: 0xc0 (VM-), Length: 24, Vnd: TGPP, Val: 738002fffeff>

# Current flat AVP representation
print("=== Current Flat AVP Representation ===")
print(message_to_json(ccr_i.message))

# Generic class-based representation for any Diameter message
def message_to_class_json(message):
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


def _avp_name_to_field_name(avp_name):
    """Convert AVP name to Python field name (snake_case)."""
    # Handle special cases and common patterns
    field_name = avp_name.lower()
    field_name = field_name.replace('-', '_')
    field_name = field_name.replace('3gpp_', '3gpp_')
    field_name = field_name.replace('cc_', 'cc_')
    field_name = field_name.replace('_id', '_id')
    return field_name


def _process_single_avp(avp):
    """Process a single AVP and return its structured value."""
    from diameter.message.avp import AvpGrouped
    
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


def _convert_byte_value(avp_name, value):
    """Convert byte values to more readable formats based on AVP type."""
    if not isinstance(value, bytes):
        return value
    
    # Handle specific AVP types that have known byte formats
    if avp_name in ['Framed-IP-Address', '3GPP-SGSN-Address']:
        # Try to decode as IPv4 address
        if len(value) == 4:
            try:
                from diameter_telecom.diameter.parse_avp import decode_framed_ip_address
                ipv4 = decode_framed_ip_address(value)
                if ipv4:
                    return f"{ipv4} ({value.hex()})"
            except:
                pass
    
    elif avp_name == 'Framed-IPv6-Prefix':
        # Try to decode as IPv6 prefix
        try:
            from diameter_telecom.diameter.parse_avp import decode_framed_ipv6
            ipv6 = decode_framed_ipv6(value)
            if ipv6:
                return f"{ipv6} ({value.hex()})"
        except:
            pass
    
    elif avp_name == '3GPP-User-Location-Info':
        # Parse user location info
        try:
            from diameter_telecom.diameter.parse_avp import parse_user_location_info_fixed
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

print("\n=== New Class-Based Representation ===")
print(message_to_class_json(ccr_i.message))
