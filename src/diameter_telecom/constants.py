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
SSNR = "SNR"  # Spending Status Notification Request
SSNA = "SNA"  # Spending Status Notification Answer
SNR = "SNR"  # Spending Status Notification Request
SNA = "SNA"  # Spending Status Notification Answer

# Device Watchdog Messages
DWR = "DWR"  # Device Watchdog Request
DWA = "DWA"  # Device Watchdog Answer

# Capabilities Exchange Messages
CER = "CER"  # Capabilities Exchange Request
CEA = "CEA"  # Capabilities Exchange Answer

DPR = "DPR"  # Disconnect Peer Request
DPA = "DPA"  # Disconnect Peer Answer


REQUESTS_CREATE_SESSION = [CCR_I, AAR, SLR]
REQUESTS_UPDATE_SESSION = [CCR_U, SSNR]
REQUESTS_REFRESH_SESSION = [RAR, ASR]
REQUESTS_TERMINATE_SESSION = [CCR_T, STR]

# Response message flow classifications
RESPONSES_CREATE_SESSION = [CCA_I, AAA, SLA]
RESPONSES_UPDATE_SESSION = [CCA_U, SSNA]
RESPONSES_REFRESH_SESSION = [RAA, ASA]
RESPONSES_TERMINATE_SESSION = [CCA_T, STA]