"""
CDP Ninja - Core CDP Client Module
Chrome DevTools Protocol WebSocket client and event management
"""

from .cdp_client import CDPClient, CDPEvent, CDPDomain, CDPConnection
from .cdp_pool import CDPConnectionPool, get_global_pool, initialize_global_pool, shutdown_global_pool

from .._version import __version__
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