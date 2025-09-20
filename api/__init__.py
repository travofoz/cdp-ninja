"""
Debug Ninja - HTTP API Server Module
Flask server exposing Chrome DevTools Protocol via REST endpoints
"""

from .server import CDPBridgeServer

__version__ = "1.0.0"
__author__ = "Debug Ninja Contributors"

__all__ = [
    'CDPBridgeServer'
]