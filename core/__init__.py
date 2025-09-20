"""
Debug Ninja - Core CDP Client Module
Chrome DevTools Protocol WebSocket client and event management
"""

from .cdp_client import CDPClient, CDPEvent, CDPDomain, CDPConnection

__version__ = "1.0.0"
__author__ = "Debug Ninja Contributors"

__all__ = [
    'CDPClient',
    'CDPEvent',
    'CDPDomain',
    'CDPConnection'
]