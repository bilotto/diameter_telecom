"""
Diameter Message Type Constants

This module defines constants for various Diameter message types used in
telecommunications networks. These constants are used to identify and
process different types of Diameter messages.

The constants are organized by message type:
- Credit Control (CCR/CCA): Initial, Update, Termination, and Event messages
- Re-Auth (RAR/RAA): Re-authorization messages
- AA (AAR/AAA): Authentication and Authorization messages
- Session Termination (STR/STA): Session termination messages
- Abort Session (ASR/ASA): Session abort messages
- Spending Limit (SLR/SLA): Spending limit messages
- Spending Status Notification (SSNR/SSNA): Spending status messages
- Device Watchdog (DWR/DWA): Connection monitoring messages
- Capabilities Exchange (CER/CEA): Node capability exchange messages
"""

from diameter.message.constants import *

# Credit Control Messages
CCR_I = "CCR-I"  # Credit Control Request - Initial
CCA_I = "CCA-I"  # Credit Control Answer - Initial
CCR_U = "CCR-U"  # Credit Control Request - Update
CCA_U = "CCA-U"  # Credit Control Answer - Update
CCR_T = "CCR-T"  # Credit Control Request - Termination
CCA_T = "CCA-T"  # Credit Control Answer - Termination
CCR_E = "CCR-E"  # Credit Control Request - Event
CCA_E = "CCA-E"  # Credit Control Answer - Event

# Re-Auth Messages
RAR = "RAR"  # Re-Auth Request
RAA = "RAA"  # Re-Auth Answer

# Authentication and Authorization Messages
AAR = "AAR"  # Authentication and Authorization Request
AAA = "AAA"  # Authentication and Authorization Answer

# Session Termination Messages
STR = "STR"  # Session Termination Request
STA = "STA"  # Session Termination Answer

# Abort Session Messages
ASR = "ASR"  # Abort Session Request
ASA = "ASA"  # Abort Session Answer

# Spending Limit Messages
SLR = "SLR"  # Spending Limit Request
SLA = "SLA"  # Spending Limit Answer

# Spending Status Notification Messages
SSNR = "SSNR"  # Spending Status Notification Request
SSNA = "SSNA"  # Spending Status Notification Answer

# Device Watchdog Messages
DWR = "DWR"  # Device Watchdog Request
DWA = "DWA"  # Device Watchdog Answer

# Capabilities Exchange Messages
CER = "CER"  # Capabilities Exchange Request
CEA = "CEA"  # Capabilities Exchange Answer
