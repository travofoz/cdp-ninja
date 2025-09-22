"""
Chrome DevTools Protocol WebSocket Client
Handles connection, command sending, and event streaming
"""

import asyncio
import json
import logging
import time
import websocket
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from queue import Queue, Empty, Full
from threading import Thread, Lock, Event
from typing import Dict, List, Optional, Any, Callable
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CDPDomain(Enum):
    """CDP Protocol Domains"""
    NETWORK = "Network"
    RUNTIME = "Runtime"
    PAGE = "Page"
    DOM = "DOM"
    DEBUGGER = "Debugger"
    CONSOLE = "Console"
    INPUT = "Input"
    SECURITY = "Security"
    FETCH = "Fetch"
    PERFORMANCE = "Performance"
    MEMORY = "Memory"


@dataclass
class CDPEvent:
    """Structured CDP Event"""
    method: str
    params: Dict[str, Any]
    domain: str
    timestamp: float
    session_id: Optional[str] = None

    @classmethod
    def from_raw(cls, data: dict):
        """Create CDPEvent from raw WebSocket message"""
        method = data.get('method', '')
        domain = method.split('.')[0] if '.' in method else 'Unknown'
        return cls(
            method=method,
            params=data.get('params', {}),
            domain=domain,
            timestamp=time.time(),
            session_id=data.get('sessionId')
        )

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class CDPConnection:
    """Manages WebSocket connection to Chrome DevTools"""

    def __init__(self, port: int = 9222, host: str = 'localhost'):
        self.port = port
        self.host = host
        self.ws: Optional[websocket.WebSocket] = None
        self.connected = Event()
        self.url: Optional[str] = None
        self._reconnect_attempts = 0
        self._max_reconnect = 5

    def get_debugger_url(self) -> Optional[str]:
        """Fetch WebSocket URL from Chrome /json endpoint"""
        try:
            response = requests.get(
                f"http://{self.host}:{self.port}/json",
                timeout=30  # Increased timeout for Windows
            )
            response.raise_for_status()
            tabs = response.json()

            if not tabs:
                logger.warning("No Chrome tabs available")
                return None

            # Prefer active tab or page type
            for tab in tabs:
                if (tab.get('type') == 'page' and
                    not tab.get('url', '').startswith('devtools://') and
                    'webSocketDebuggerUrl' in tab):
                    logger.info(f"Selected tab: {tab.get('title', 'Untitled')} - {tab.get('url')}")
                    return tab['webSocketDebuggerUrl']

            # Fallback to first available
            if tabs and 'webSocketDebuggerUrl' in tabs[0]:
                return tabs[0]['webSocketDebuggerUrl']

            logger.error("No valid WebSocket debugger URL found")
            return None

        except requests.RequestException as e:
            logger.error(f"Failed to get debugger URL: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting debugger URL: {e}")
            return None

    def connect(self) -> bool:
        """Establish WebSocket connection"""
        try:
            self.url = self.get_debugger_url()
            if not self.url:
                logger.error("No Chrome WebSocket URL available")
                return False

            self.ws = websocket.WebSocket()
            self.ws.settimeout(10)
            self.ws.connect(self.url)

            self.connected.set()
            self._reconnect_attempts = 0
            logger.info(f"Connected to Chrome DevTools: {self.url}")
            return True

        except websocket.WebSocketException as e:
            logger.error(f"WebSocket connection failed: {e}")
            self.connected.clear()
            return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.connected.clear()
            return False

    def reconnect(self) -> bool:
        """Attempt to reconnect with exponential backoff"""
        if self._reconnect_attempts >= self._max_reconnect:
            logger.error(f"Max reconnection attempts ({self._max_reconnect}) reached")
            return False

        wait_time = min(2 ** self._reconnect_attempts, 30)
        logger.info(f"Reconnecting in {wait_time}s (attempt {self._reconnect_attempts + 1}/{self._max_reconnect})")
        time.sleep(wait_time)

        self._reconnect_attempts += 1
        return self.connect()

    def disconnect(self):
        """Close WebSocket connection"""
        if self.ws:
            try:
                self.ws.close()
            except Exception as e:
                logger.debug(f"Error closing WebSocket: {e}")
                pass
            self.connected.clear()
            self.ws = None
            logger.info("Disconnected from Chrome DevTools")

    def send(self, message: str) -> bool:
        """Send message to Chrome DevTools"""
        if not self.connected.is_set() or not self.ws:
            return False

        try:
            self.ws.send(message)
            return True
        except websocket.WebSocketException as e:
            logger.error(f"Failed to send message: {e}")
            self.connected.clear()
            return False

    def receive(self, timeout: float = 1.0) -> Optional[str]:
        """Receive message from Chrome DevTools"""
        if not self.connected.is_set() or not self.ws:
            return None

        try:
            self.ws.settimeout(timeout)
            message = self.ws.recv()
            return message
        except websocket.WebSocketTimeoutException:
            return None
        except websocket.WebSocketConnectionClosedException:
            logger.warning("WebSocket connection closed")
            self.connected.clear()
            return None
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            return None


class CDPClient:
    """High-level CDP Client with event management and command execution"""

    def __init__(self,
                 port: int = 9222,
                 host: str = 'localhost',
                 max_events: int = 1000,
                 auto_reconnect: bool = True):

        self.connection = CDPConnection(port, host)
        self.auto_reconnect = auto_reconnect

        # Event management
        self.max_events = max_events
        self.event_queue = Queue(maxsize=max_events)
        self.events_by_domain = defaultdict(lambda: deque(maxlen=100))
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)

        # Command tracking
        self.command_id = 1
        self.pending_commands: Dict[int, dict] = {}
        self.command_lock = Lock()

        # Background thread for receiving messages
        self.listener_thread: Optional[Thread] = None
        self.running = False

    def start(self) -> bool:
        """Initialize connection and start listening"""
        logger.info("Starting CDP client...")

        if not self.connection.connect():
            logger.error("Failed to connect to Chrome DevTools")
            return False

        self.running = True
        self.listener_thread = Thread(target=self._listen_loop, daemon=True)
        self.listener_thread.start()

        # Enable essential domains
        if not self._enable_default_domains():
            logger.warning("Failed to enable some CDP domains")

        logger.info("CDP client started successfully")
        return True

    def stop(self):
        """Stop client and cleanup"""
        logger.info("Stopping CDP client...")
        self.running = False

        if self.connection:
            self.connection.disconnect()

        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=5)

        logger.info("CDP client stopped")

    def _listen_loop(self):
        """Background thread to receive and process CDP messages"""
        logger.info("Starting CDP message listener")

        while self.running:
            try:
                if not self.connection.connected.is_set():
                    if self.auto_reconnect:
                        logger.info("Attempting to reconnect...")
                        if not self.connection.reconnect():
                            logger.error("Reconnection failed, stopping listener")
                            break
                        # Re-enable domains after reconnect
                        self._enable_default_domains()
                    else:
                        logger.info("Connection lost, stopping listener")
                        break

                message = self.connection.receive(timeout=0.5)
                if message:
                    self._process_message(message)

            except Exception as e:
                logger.error(f"Error in listen loop: {e}")

        logger.info("CDP message listener stopped")

    def _process_message(self, message: str):
        """Route CDP message to appropriate handler"""
        try:
            data = json.loads(message)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            return

        if 'id' in data:
            # Command response
            self._handle_command_response(data)
        else:
            # Event from browser
            event = CDPEvent.from_raw(data)
            self._handle_event(event)

    def _handle_command_response(self, data: dict):
        """Handle response to a command we sent"""
        cmd_id = data['id']
        with self.command_lock:
            if cmd_id in self.pending_commands:
                self.pending_commands[cmd_id]['response'] = data
                self.pending_commands[cmd_id]['event'].set()

    def _handle_event(self, event: CDPEvent):
        """Process and distribute CDP events"""
        # Store in domain-specific queue
        self.events_by_domain[event.domain].append(event)

        # Add to general queue (non-blocking, drop if full)
        try:
            self.event_queue.put_nowait(event)
        except Full:
            logger.debug(f"Event queue full, dropping {event.method} event")
            pass

        # Trigger registered handlers
        for handler in self.event_handlers.get(event.method, []):
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler error for {event.method}: {e}")

    def send_command(self, method: str, params: Optional[dict] = None,
                    timeout: float = 10) -> dict:
        """Send CDP command and wait for response"""
        if not self.connection.connected.is_set():
            return {"error": "Not connected to Chrome DevTools"}

        with self.command_lock:
            cmd_id = self.command_id
            self.command_id += 1

            command = {
                "id": cmd_id,
                "method": method
            }
            if params:
                command["params"] = params

            response_event = Event()
            self.pending_commands[cmd_id] = {
                "command": command,
                "response": None,
                "event": response_event
            }

        try:
            # Send command
            message = json.dumps(command)
            if not self.connection.send(message):
                with self.command_lock:
                    if cmd_id in self.pending_commands:
                        del self.pending_commands[cmd_id]
                return {"error": "Failed to send command"}

            # Wait for response
            if response_event.wait(timeout):
                with self.command_lock:
                    response = self.pending_commands[cmd_id]['response']
                    del self.pending_commands[cmd_id]

                if 'error' in response:
                    logger.warning(f"CDP command error: {method} - {response['error']}")

                return response
            else:
                # Timeout
                with self.command_lock:
                    if cmd_id in self.pending_commands:
                        del self.pending_commands[cmd_id]
                return {"error": f"Command timeout after {timeout}s"}

        except Exception as e:
            logger.error(f"Error sending command {method}: {e}")
            return {"error": str(e)}

    def _enable_default_domains(self) -> bool:
        """Enable essential CDP domains"""
        domains = [
            CDPDomain.NETWORK,
            CDPDomain.RUNTIME,
            CDPDomain.PAGE,
            CDPDomain.DOM,
            CDPDomain.CONSOLE,
            CDPDomain.INPUT
        ]

        success_count = 0
        for domain in domains:
            result = self.send_command(f"{domain.value}.enable", timeout=5)
            if 'error' not in result:
                logger.debug(f"Enabled {domain.value} domain")
                success_count += 1
            else:
                logger.warning(f"Failed to enable {domain.value}: {result.get('error')}")

        logger.info(f"Enabled {success_count}/{len(domains)} CDP domains")
        return success_count == len(domains)

    def register_event_handler(self, method: str, handler: Callable[[CDPEvent], None]):
        """Register callback for specific CDP event"""
        self.event_handlers[method].append(handler)
        logger.debug(f"Registered handler for {method}")

    def get_recent_events(self, domain: Optional[str] = None, limit: int = 50) -> List[CDPEvent]:
        """Get recent events, optionally filtered by domain"""
        if domain:
            events = list(self.events_by_domain[domain])
            return events[-limit:] if events else []
        else:
            events = []
            try:
                while not self.event_queue.empty() and len(events) < limit:
                    events.append(self.event_queue.get_nowait())
            except Empty:
                pass
            return events

    def clear_events(self, domain: Optional[str] = None):
        """Clear stored events"""
        if domain:
            self.events_by_domain[domain].clear()
        else:
            # Clear all events
            with self.event_queue.mutex:
                self.event_queue.queue.clear()
            for domain_queue in self.events_by_domain.values():
                domain_queue.clear()

    def is_connected(self) -> bool:
        """Check if connected to Chrome DevTools"""
        return self.connection.connected.is_set()

    def get_connection_info(self) -> dict:
        """Get connection information"""
        return {
            "connected": self.is_connected(),
            "host": self.connection.host,
            "port": self.connection.port,
            "url": self.connection.url,
            "events_queued": self.event_queue.qsize(),
            "domains_active": list(self.events_by_domain.keys())
        }


# Convenience functions for common operations
def create_cdp_client(port: int = 9222, auto_start: bool = True) -> CDPClient:
    """Create and optionally start a CDP client"""
    client = CDPClient(port=port)
    if auto_start:
        client.start()
    return client


def test_chrome_connection(port: int = 9222) -> bool:
    """Test if Chrome DevTools is accessible on given port"""
    try:
        response = requests.get(f"http://localhost:{port}/json", timeout=2)
        tabs = response.json()
        return len(tabs) > 0
    except (requests.RequestException, ValueError, KeyError) as e:
        logger.debug(f"Chrome connection test failed on port {port}: {e}")
        return False


if __name__ == "__main__":
    # Simple test of CDP client
    print("Testing CDP Client...")

    if not test_chrome_connection():
        print("❌ Chrome DevTools not accessible on port 9222")
        print("Start Chrome with: chrome --remote-debugging-port=9222")
        exit(1)

    client = create_cdp_client()

    if client.is_connected():
        print("✅ Connected to Chrome DevTools")

        # Test basic command
        result = client.send_command("Runtime.evaluate", {
            "expression": "navigator.userAgent"
        })

        if 'result' in result and 'result' in result['result']:
            print(f"✅ Browser: {result['result']['result']['value']}")
        else:
            print("❌ Failed to execute test command")

        # Show connection info
        info = client.get_connection_info()
        print(f"ℹ️ Connection info: {info}")

        client.stop()
    else:
        print("❌ Failed to connect to Chrome DevTools")