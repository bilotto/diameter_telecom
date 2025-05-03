"""
Diameter Protocol Implementation Module

This module extends the base diameter library with telecom-specific functionality.
It provides implementations for various Diameter applications (Gx, Rx, Sy) and
session management for telecommunications networks.

The module builds upon the base diameter library by:
1. Adding telecom-specific message handling and parsing
2. Implementing standard Diameter applications used in telecom networks
3. Providing session management for different Diameter applications
4. Adding helper functions for node and peer management
5. Defining telecom-specific constants and message types

Key Components:
- Applications: Gx, Rx, and Sy implementations for policy control and charging
- Sessions: Session management for different Diameter applications
- Messages: Enhanced message handling with telecom-specific attributes
- Helpers: Utility functions for node and peer configuration
- Constants: Telecom-specific Diameter message and AVP constants
"""

from ..subscriber import Subscriber

from .helpers import create_node, add_peers, add_peer_to_node

from .app import GxApplication, RxApplication, SyApplication

from .session import GxSession, RxSession, SySession

from .message import DiameterMessage

from .constants import *
