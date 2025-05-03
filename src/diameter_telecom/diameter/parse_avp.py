from typing import List
from diameter.message.constants import *
from diameter.message.avp.grouped import SubscriptionId
from ..diameter_message import DiameterMessage

import logging
logger = logging.getLogger(__name__)

def parse_subscription_id(subscription_id: List[SubscriptionId]):
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
def bytes_to_ip(ip_bytes):
    try:
        return socket.inet_ntoa(ip_bytes)
    except:
        logger.error(f"Error converting bytes to IP: {ip_bytes}")
        return None
    
import ipaddress
def decode_framed_ipv6(raw_bytes):
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
    

def check_charging_rule_remove(diameter_message: DiameterMessage):
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

def check_charging_rule_install(diameter_message: DiameterMessage):
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


def check_qos(diameter_message: DiameterMessage):
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

def check_event_trigger(diameter_message: DiameterMessage):
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

def check_rat_type(diameter_message: DiameterMessage):
    message = diameter_message.message
    try:
        if hasattr(message, "rat_type") and message.rat_type:
            return message.rat_type
    except:
        logger.error(f"Error then trying to set RAT Type from GxSession")
        pass


