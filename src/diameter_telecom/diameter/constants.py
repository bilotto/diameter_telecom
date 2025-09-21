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

# Import specific constants from diameter library
try:
    from diameter.message.constants import (
        DIAMETER_SUCCESS,
        DIAMETER_UNABLE_TO_DELIVER,
        DIAMETER_REALM_NOT_SERVED,
        DIAMETER_TOO_BUSY,
        DIAMETER_LOOP_DETECTED,
        DIAMETER_REDIRECT_INDICATION,
        DIAMETER_APPLICATION_UNSUPPORTED,
        DIAMETER_INVALID_HDR_BITS,
        DIAMETER_INVALID_AVP_BITS,
        DIAMETER_UNKNOWN_PEER,
        DIAMETER_AUTHENTICATION_REJECTED,
        DIAMETER_OUT_OF_SPACE,
        DIAMETER_ELECTION_LOST,
        DIAMETER_AVP_UNSUPPORTED,
        DIAMETER_UNKNOWN_SESSION_ID,
        DIAMETER_AUTHORIZATION_REJECTED,
        DIAMETER_AVP_OCCURS_TOO_MANY_TIMES,
        DIAMETER_NO_COMMON_APPLICATION,
        DIAMETER_UNSUPPORTED_VERSION,
        DIAMETER_UNABLE_TO_COMPLY,
        DIAMETER_INVALID_AVP_VALUE,
        DIAMETER_MISSING_AVP,
        DIAMETER_RESOURCES_EXCEEDED,
        DIAMETER_CONTRADICTING_AVPS,
        DIAMETER_AVP_NOT_ALLOWED,
        DIAMETER_AVP_IS_ONLY_ALLOWED,
        DIAMETER_UNKNOWN_AVP,
        DIAMETER_NO_COMMON_SECURITY,
        DIAMETER_UNKNOWN_PEER,
        DIAMETER_AUTHENTICATION_REJECTED,
        DIAMETER_OUT_OF_SPACE,
        DIAMETER_ELECTION_LOST,
        DIAMETER_AVP_UNSUPPORTED,
        DIAMETER_UNKNOWN_SESSION_ID,
        DIAMETER_AUTHORIZATION_REJECTED,
        DIAMETER_AVP_OCCURS_TOO_MANY_TIMES,
        DIAMETER_NO_COMMON_APPLICATION,
        DIAMETER_UNSUPPORTED_VERSION,
        DIAMETER_UNABLE_TO_COMPLY,
        DIAMETER_INVALID_AVP_VALUE,
        DIAMETER_MISSING_AVP,
        DIAMETER_RESOURCES_EXCEEDED,
        DIAMETER_CONTRADICTING_AVPS,
        DIAMETER_AVP_NOT_ALLOWED,
        DIAMETER_AVP_IS_ONLY_ALLOWED,
        DIAMETER_UNKNOWN_AVP,
        DIAMETER_NO_COMMON_SECURITY,
        APP_3GPP_GX,
        APP_3GPP_RX,
        APP_3GPP_SY,
        CCR_INITIAL,
        CCR_UPDATE,
        CCR_TERMINATION,
        CCR_EVENT,
        CCA_INITIAL,
        CCA_UPDATE,
        CCA_TERMINATION,
        CCA_EVENT,
        RAR,
        RAA,
        AAR,
        AAA,
        STR,
        STA,
        ASR,
        ASA,
        SLR,
        SLA,
        SSNR,
        SSNA,
        DWR,
        DWA,
        CER,
        CEA,
        DPR,
        DPA
    )
except ImportError:
    # Fallback constants if diameter library is not available
    DIAMETER_SUCCESS = 2001
    DIAMETER_UNABLE_TO_DELIVER = 3002
    DIAMETER_REALM_NOT_SERVED = 3003
    DIAMETER_TOO_BUSY = 3004
    DIAMETER_LOOP_DETECTED = 3005
    DIAMETER_REDIRECT_INDICATION = 3006
    DIAMETER_APPLICATION_UNSUPPORTED = 3007
    DIAMETER_INVALID_HDR_BITS = 3008
    DIAMETER_INVALID_AVP_BITS = 3009
    DIAMETER_UNKNOWN_PEER = 3010
    DIAMETER_AUTHENTICATION_REJECTED = 4001
    DIAMETER_OUT_OF_SPACE = 4002
    DIAMETER_ELECTION_LOST = 4003
    DIAMETER_AVP_UNSUPPORTED = 5001
    DIAMETER_UNKNOWN_SESSION_ID = 5002
    DIAMETER_AUTHORIZATION_REJECTED = 5003
    DIAMETER_AVP_OCCURS_TOO_MANY_TIMES = 5004
    DIAMETER_NO_COMMON_APPLICATION = 5005
    DIAMETER_UNSUPPORTED_VERSION = 5006
    DIAMETER_UNABLE_TO_COMPLY = 5007
    DIAMETER_INVALID_AVP_VALUE = 5008
    DIAMETER_MISSING_AVP = 5009
    DIAMETER_RESOURCES_EXCEEDED = 5010
    DIAMETER_CONTRADICTING_AVPS = 5011
    DIAMETER_AVP_NOT_ALLOWED = 5012
    DIAMETER_AVP_IS_ONLY_ALLOWED = 5013
    DIAMETER_UNKNOWN_AVP = 5014
    DIAMETER_NO_COMMON_SECURITY = 5015
    APP_3GPP_GX = 16777238
    APP_3GPP_RX = 16777236
    APP_3GPP_SY = 16777202
    CCR_INITIAL = 272
    CCR_UPDATE = 272
    CCR_TERMINATION = 272
    CCR_EVENT = 272
    CCA_INITIAL = 272
    CCA_UPDATE = 272
    CCA_TERMINATION = 272
    CCA_EVENT = 272
    RAR = 258
    RAA = 258
    AAR = 265
    AAA = 265
    STR = 275
    STA = 275
    ASR = 274
    ASA = 274
    SLR = 8388622
    SLA = 8388622
    SSNR = 8388623
    SSNA = 8388623
    DWR = 280
    DWA = 280
    CER = 257
    CEA = 257
    DPR = 282
    DPA = 282

# Credit Control Messages
CCR_I = "CCR-I"  # Credit Control Request - Initial
CCA_I = "CCA-I"  # Credit Control Answer - Initial
CCR_U = "CCR-U"  # Credit Control Request - Update
CCA_U = "CCA-U"  # Credit Control Answer - Update
CCR_T = "CCR-T"  # Credit Control Request - Termination
CCA_T = "CCA-T"  # Credit Control Answer - Termination
CCR_E = "CCR-E"  # Credit Control Request - Event
CCA_E = "CCA-E"  # Credit Control Answer - Event
CCR = "CCR"  # Credit Control Request
CCA = "CCA"  # Credit Control Answer

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

DPR = "DPR"  # Disconnect Peer Request
DPA = "DPA"  # Disconnect Peer Answer


REQUESTS_CREATE_SESSION = [CCR_I, AAR, SLR]
RESPONSES_END_SESSION = [STA, CCA_T]
