"""
CDP Connection Pool - For performance only
Reuses connections, doesn't validate anything
The goal is speed and resource efficiency, not safety
"""

import logging
import threading
import time
from queue import Queue, Empty
from typing import Optional, Dict, Any

from .cdp_client import CDPClient

logger = logging.getLogger(__name__)


class CDPConnectionPool:
    """
    Raw connection pool - no safety, just performance
    Manages multiple CDP connections for concurrent operations

    @class CDPConnectionPool
    @property {Queue} pool - Available connections
    @property {dict} in_use - Connections currently in use
    @property {int} max_connections - Maximum concurrent connections
    @property {int} port - Chrome DevTools port
    @property {threading.Lock} lock - Thread safety lock
    """

    def __init__(self, max_connections: int = 5, port: int = 9222, auto_reconnect: bool = True):
        """
        Initialize connection pool

        @param {int} max_connections - Max concurrent connections to Chrome
        @param {int} port - Chrome DevTools Protocol port
        @param {bool} auto_reconnect - Whether to auto-reconnect dead connections
        """
        self.max_connections = max_connections
        self.port = port
        self.auto_reconnect = auto_reconnect

        # Connection management
        self.pool = Queue(maxsize=max_connections)
        self.in_use: Dict[str, CDPClient] = {}
        self.lock = threading.Lock()

        # Statistics
        self.stats = {
            'total_created': 0,
            'total_acquired': 0,
            'total_released': 0,
            'connection_failures': 0,
            'current_in_use': 0
        }

        # Create initial connections
        self._initialize_pool()

    def _initialize_pool(self):
        """
        Create initial pool of CDP connections

        @private
        """
        logger.info(f"🔗 Initializing CDP pool with {self.max_connections} connections")

        for i in range(self.max_connections):
            try:
                client = CDPClient(
                    port=self.port,
                    max_events=10000,  # Big buffer for stress testing
                    auto_reconnect=self.auto_reconnect
                )

                if client.start():
                    self.pool.put(client)
                    self.stats['total_created'] += 1
                    logger.debug(f"✓ Connection {i+1}/{self.max_connections} ready")
                else:
                    logger.warning(f"✗ Connection {i+1} failed to start")
                    self.stats['connection_failures'] += 1

            except Exception as e:
                logger.error(f"✗ Connection {i+1} creation failed: {e}")
                self.stats['connection_failures'] += 1

        available = self.pool.qsize()
        logger.info(f"🔗 Pool initialized: {available}/{self.max_connections} connections available")

        if available == 0:
            logger.error("🚨 NO CDP connections available! Check if Chrome is running with --remote-debugging-port")

    def acquire(self, timeout: float = 30.0) -> Optional[CDPClient]:
        """
        Get connection from pool or timeout
        Long timeout allows for heavy fuzzing operations

        @param {float} timeout - Max time to wait for connection
        @returns {CDPClient|None} Available connection or None if exhausted
        @throws {Exception} When all connections are exhausted/dead
        """
        try:
            client = self.pool.get(timeout=timeout)

            # Check if connection is still alive
            if not client.is_connected():
                logger.warning("🔄 Got dead connection from pool, attempting to revive")
                if self._try_revive_connection(client):
                    logger.info("✅ Connection revived successfully")
                else:
                    logger.error("💀 Connection revival failed, trying to create new one")
                    client = self._create_new_connection()
                    if not client:
                        raise Exception("Failed to create replacement connection")

            # Track usage
            with self.lock:
                connection_id = str(id(client))
                self.in_use[connection_id] = client
                self.stats['total_acquired'] += 1
                self.stats['current_in_use'] = len(self.in_use)

            logger.debug(f"📤 Connection acquired (in use: {self.stats['current_in_use']})")
            return client

        except Empty:
            # All connections busy - that's debugging data too!
            logger.error(f"🚨 All {self.max_connections} CDP connections exhausted!")
            logger.error("This could indicate:")
            logger.error("  - Chrome is hanging/crashed")
            logger.error("  - Too many concurrent operations")
            logger.error("  - Infinite loops in JavaScript")

            raise Exception(
                f"All {self.max_connections} CDP connections exhausted. "
                f"Chrome may be unresponsive or there are too many concurrent operations."
            )

    def release(self, client: CDPClient):
        """
        Return connection to pool if it's still alive
        Dead connections get replaced automatically

        @param {CDPClient} client - Client to release back to pool
        """
        if not client:
            logger.warning("⚠️  Attempted to release None client")
            return

        connection_id = str(id(client))

        with self.lock:
            if connection_id not in self.in_use:
                logger.warning("⚠️  Attempted to release connection not in use")
                return

            del self.in_use[connection_id]
            self.stats['total_released'] += 1
            self.stats['current_in_use'] = len(self.in_use)

        # Check if connection is still alive before returning to pool
        if client.is_connected():
            self.pool.put(client)
            logger.debug(f"📥 Connection released (in use: {self.stats['current_in_use']})")
        else:
            # Connection died - spawn replacement
            logger.warning("💀 Released connection is dead, creating replacement")
            replacement = self._create_new_connection()
            if replacement:
                self.pool.put(replacement)
                logger.info("✅ Dead connection replaced")
            else:
                logger.error("❌ Failed to replace dead connection")

    def _try_revive_connection(self, client: CDPClient) -> bool:
        """
        Try to revive a dead connection

        @param {CDPClient} client - Dead connection to revive
        @returns {bool} True if successfully revived
        @private
        """
        try:
            client.stop()
            time.sleep(0.1)  # Brief pause
            return client.start()
        except Exception as e:
            logger.error(f"Connection revival failed: {e}")
            return False

    def _create_new_connection(self) -> Optional[CDPClient]:
        """
        Create a new CDP connection

        @returns {CDPClient|None} New connection or None if failed
        @private
        """
        try:
            client = CDPClient(
                port=self.port,
                max_events=10000,
                auto_reconnect=self.auto_reconnect
            )

            if client.start():
                self.stats['total_created'] += 1
                logger.debug("✅ New connection created")
                return client
            else:
                logger.warning("❌ New connection failed to start")
                self.stats['connection_failures'] += 1
                return None

        except Exception as e:
            logger.error(f"New connection creation failed: {e}")
            self.stats['connection_failures'] += 1
            return None

    def get_stats(self) -> Dict[str, Any]:
        """
        Get connection pool statistics

        @returns {dict} Pool statistics and health info
        """
        with self.lock:
            current_in_use = len(self.in_use)

        return {
            'max_connections': self.max_connections,
            'available': self.pool.qsize(),
            'in_use': current_in_use,
            'total_created': self.stats['total_created'],
            'total_acquired': self.stats['total_acquired'],
            'total_released': self.stats['total_released'],
            'connection_failures': self.stats['connection_failures'],
            'pool_health': 'HEALTHY' if self.pool.qsize() > 0 else 'EXHAUSTED',
            'chrome_responsive': current_in_use < self.max_connections
        }

    def force_refresh_pool(self):
        """
        Force refresh all connections (useful if Chrome restarted)
        This is a debugging tool - use when Chrome has been restarted
        """
        logger.info("🔄 Force refreshing entire connection pool")

        # Clear current pool
        while not self.pool.empty():
            try:
                old_client = self.pool.get_nowait()
                old_client.stop()
            except Exception as e:
                logger.debug(f"Error stopping old client during refresh: {e}")
                pass

        # Clear in-use connections (they're probably dead anyway)
        with self.lock:
            for client in self.in_use.values():
                try:
                    client.stop()
                except Exception as e:
                    logger.debug(f"Error stopping in-use client during refresh: {e}")
                    pass
            self.in_use.clear()

        # Reinitialize
        self._initialize_pool()
        logger.info("🔄 Pool refresh complete")

    def shutdown(self):
        """
        Shutdown all connections in pool
        """
        logger.info("🛑 Shutting down CDP connection pool")

        # Shutdown pool connections
        while not self.pool.empty():
            try:
                client = self.pool.get_nowait()
                client.stop()
            except Exception as e:
                logger.debug(f"Error stopping client during shutdown: {e}")
                pass

        # Shutdown in-use connections
        with self.lock:
            for client in self.in_use.values():
                try:
                    client.stop()
                except Exception as e:
                    logger.debug(f"Error stopping in-use client during shutdown: {e}")
                    pass
            self.in_use.clear()

        logger.info("🛑 CDP pool shutdown complete")


# Global pool instance (will be initialized by main app)
_global_pool: Optional[CDPConnectionPool] = None


def get_global_pool() -> Optional[CDPConnectionPool]:
    """
    Get the global CDP connection pool

    @returns {CDPConnectionPool|None} Global pool instance
    """
    return _global_pool


def initialize_global_pool(max_connections: int = 5, port: int = 9222) -> CDPConnectionPool:
    """
    Initialize the global CDP connection pool

    @param {int} max_connections - Maximum concurrent connections
    @param {int} port - Chrome DevTools port
    @returns {CDPConnectionPool} Initialized pool
    """
    global _global_pool
    _global_pool = CDPConnectionPool(max_connections=max_connections, port=port)
    return _global_pool


def shutdown_global_pool():
    """
    Shutdown the global connection pool
    """
    global _global_pool
    if _global_pool:
        _global_pool.shutdown()
        _global_pool = None