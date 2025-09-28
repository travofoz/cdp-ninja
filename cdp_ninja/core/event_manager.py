"""
Centralized Event Manager for CDP Ninja

Handles event storage and retrieval across all CDPClient instances.
Provides thread-safe, centralized event management to fix the architectural
issue where events were fragmented across multiple client instances.
"""

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock, RLock
from typing import Dict, List, Optional, Any, Callable
from queue import Queue, Empty, Full

# Import CDPEvent from cdp_client to avoid circular imports
# This will be imported when cdp_client imports this module
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .cdp_client import CDPEvent

logger = logging.getLogger(__name__)

# Global event manager instance
_global_event_manager: Optional['EventManager'] = None
_event_manager_lock = RLock()


class EventManager:
    """
    Centralized event storage and management for all CDPClient instances.

    Provides thread-safe event storage that can be shared across multiple
    CDPClient connections while maintaining proper domain isolation.
    """

    def __init__(self, max_events_per_domain: int = 100, max_total_events: int = 10000):
        """
        Initialize centralized event manager

        Args:
            max_events_per_domain: Maximum events to store per domain
            max_total_events: Maximum total events across all domains
        """
        self.max_events_per_domain = max_events_per_domain
        self.max_total_events = max_total_events

        # Thread-safe event storage
        self.events_by_domain: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_events_per_domain)
        )
        self.event_queue = Queue(maxsize=max_total_events)

        # Event handlers - domain-specific callbacks
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)

        # Thread safety
        self.lock = RLock()

        # Event statistics
        self.total_events_received = 0
        self.events_dropped = 0

        logger.info(f"EventManager initialized with {max_events_per_domain} events per domain, {max_total_events} total")

    def store_event(self, event: 'CDPEvent') -> bool:
        """
        Store an event in centralized storage

        Args:
            event: CDPEvent to store

        Returns:
            bool: True if stored successfully, False if dropped
        """
        with self.lock:
            # Import here to avoid circular imports
            from .domain_manager import get_domain_manager

            # Only store events for enabled domains
            domain_manager = get_domain_manager()
            if not domain_manager:
                logger.warning("No domain manager available, storing event anyway")
            else:
                # Check if domain is enabled (convert string domain to enum if needed)
                domain_enabled = False
                try:
                    from .domain_manager import CDPDomain
                    for enabled_domain in domain_manager.enabled_domains:
                        if enabled_domain.value == event.domain:
                            domain_enabled = True
                            break
                except Exception as e:
                    logger.debug(f"Error checking domain enabled status: {e}")
                    # Fall back to storing event anyway
                    domain_enabled = True

                if not domain_enabled:
                    logger.debug(f"Dropping event for disabled domain: {event.domain}")
                    return False

            # Store in domain-specific queue
            self.events_by_domain[event.domain].append(event)

            # Store in general event queue (non-blocking, drop if full)
            try:
                self.event_queue.put_nowait(event)
            except Full:
                self.events_dropped += 1
                logger.debug(f"Event queue full, dropped {event.method} event (total dropped: {self.events_dropped})")

            # Update statistics
            self.total_events_received += 1

            # Trigger registered handlers
            for handler in self.event_handlers.get(event.method, []):
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Event handler error for {event.method}: {e}")

            logger.debug(f"Stored event: {event.method} in domain {event.domain}")
            return True

    def get_recent_events(self, domain: Optional[str] = None, limit: int = 50) -> List['CDPEvent']:
        """
        Get recent events, optionally filtered by domain

        Args:
            domain: Domain to filter by (None for all domains)
            limit: Maximum number of events to return

        Returns:
            List of CDPEvent objects
        """
        with self.lock:
            if domain:
                # Get events from specific domain
                events = list(self.events_by_domain[domain])
                return events[-limit:] if events else []
            else:
                # Get events from general queue
                events = []
                try:
                    # Create a temporary list to preserve queue order
                    temp_events = []
                    while not self.event_queue.empty() and len(temp_events) < limit:
                        temp_events.append(self.event_queue.get_nowait())

                    # Put events back in queue (FIFO order)
                    for event in temp_events:
                        try:
                            self.event_queue.put_nowait(event)
                        except Full:
                            # Queue refill failed, event is lost
                            self.events_dropped += 1
                            pass

                    # Return most recent events
                    events = temp_events[-limit:] if temp_events else []

                except Empty:
                    pass

                return events

    def clear_events(self, domain: Optional[str] = None):
        """
        Clear stored events

        Args:
            domain: Domain to clear (None for all domains)
        """
        with self.lock:
            if domain:
                self.events_by_domain[domain].clear()
                logger.info(f"Cleared events for domain: {domain}")
            else:
                # Clear all events
                with self.event_queue.mutex:
                    self.event_queue.queue.clear()

                for domain_queue in self.events_by_domain.values():
                    domain_queue.clear()

                logger.info("Cleared all events")

    def register_event_handler(self, method: str, handler: Callable[['CDPEvent'], None]):
        """
        Register callback for specific CDP event

        Args:
            method: CDP method name (e.g., 'Console.messageAdded')
            handler: Callback function
        """
        with self.lock:
            self.event_handlers[method].append(handler)
            logger.debug(f"Registered event handler for {method}")

    def unregister_event_handler(self, method: str, handler: Callable[['CDPEvent'], None]):
        """
        Unregister callback for specific CDP event

        Args:
            method: CDP method name
            handler: Callback function to remove
        """
        with self.lock:
            if handler in self.event_handlers[method]:
                self.event_handlers[method].remove(handler)
                logger.debug(f"Unregistered event handler for {method}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get event manager statistics

        Returns:
            Dictionary with statistics
        """
        with self.lock:
            domain_counts = {}
            for domain, events in self.events_by_domain.items():
                domain_counts[domain] = len(events)

            return {
                "total_events_received": self.total_events_received,
                "events_dropped": self.events_dropped,
                "current_queue_size": self.event_queue.qsize(),
                "domains_with_events": domain_counts,
                "event_handlers_registered": {
                    method: len(handlers) for method, handlers in self.event_handlers.items()
                }
            }

    def shutdown(self):
        """Clean shutdown of event manager"""
        with self.lock:
            self.clear_events()
            self.event_handlers.clear()
            logger.info("EventManager shut down")


def initialize_event_manager(max_events_per_domain: int = 100, max_total_events: int = 10000) -> EventManager:
    """
    Initialize global event manager

    Args:
        max_events_per_domain: Maximum events per domain
        max_total_events: Maximum total events

    Returns:
        EventManager instance
    """
    global _global_event_manager

    with _event_manager_lock:
        if _global_event_manager is None:
            _global_event_manager = EventManager(max_events_per_domain, max_total_events)
            logger.info("Global EventManager initialized")
        else:
            logger.warning("EventManager already initialized")

        return _global_event_manager


def get_event_manager() -> Optional[EventManager]:
    """
    Get global event manager instance

    Returns:
        EventManager instance or None if not initialized
    """
    global _global_event_manager

    with _event_manager_lock:
        if _global_event_manager is None:
            logger.warning("EventManager not initialized, auto-initializing")
            return initialize_event_manager()

        return _global_event_manager


def shutdown_event_manager():
    """Shutdown global event manager"""
    global _global_event_manager

    with _event_manager_lock:
        if _global_event_manager:
            _global_event_manager.shutdown()
            _global_event_manager = None
            logger.info("Global EventManager shut down")