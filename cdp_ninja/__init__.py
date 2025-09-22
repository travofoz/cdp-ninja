"""
🥷 CDP Ninja - Chrome DevTools Protocol Bridge
Lightweight browser debugging and security testing toolkit

Raw pass-through design for vulnerability research and fuzzing.
INTENTIONALLY DANGEROUS - Use only in isolated environments.
"""

from .server import CDPBridgeServer
from .core.cdp_client import CDPClient
from .core.cdp_pool import CDPConnectionPool, get_global_pool

__version__ = "1.0.1"
__author__ = "CDP Ninja Contributors"
__description__ = "🥷 Lightweight Chrome DevTools Protocol bridge for browser debugging and security testing"

__all__ = [
    'CDPBridgeServer',
    'CDPClient',
    'CDPConnectionPool',
    'get_global_pool'
]