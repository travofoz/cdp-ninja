"""
CDP Ninja - Core CDP Client Module
Chrome DevTools Protocol WebSocket client and event management
"""

from .cdp_client import CDPClient, CDPEvent, CDPDomain, CDPConnection
from .cdp_pool import CDPConnectionPool, get_global_pool, initialize_global_pool, shutdown_global_pool

__version__ = "1.0.0"
__author__ = "CDP Ninja Contributors"

__all__ = [
    'CDPClient',
    'CDPEvent',
    'CDPDomain',
    'CDPConnection',
    'CDPConnectionPool',
    'get_global_pool',
    'initialize_global_pool',
    'shutdown_global_pool'
]