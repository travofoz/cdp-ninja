"""
CDP Ninja Constants
Centralized configuration values and magic numbers
"""


class CDPDefaults:
    """Default values for CDP operations"""

    # Event limits
    DOMAIN_EVENTS_LIMIT = 100
    ALL_EVENTS_LIMIT = 200
    CONSOLE_EVENTS_LIMIT = 100
    NETWORK_EVENTS_LIMIT = 200

    # UI interaction defaults
    DEFAULT_SCROLL_AMOUNT = 100
    MOUSE_WHEEL_X = 100
    MOUSE_WHEEL_Y = 100

    # Screenshot settings
    DEFAULT_SCREENSHOT_QUALITY = 80
    DEFAULT_SCREENSHOT_FORMAT = "png"

    # Network simulation defaults
    DEFAULT_DOWNLOAD_THROUGHPUT = 100000  # bytes/sec
    DEFAULT_UPLOAD_THROUGHPUT = 50000     # bytes/sec
    DEFAULT_NETWORK_LATENCY = 100         # milliseconds

    # System operation timeouts
    POWERSHELL_TIMEOUT = 10              # seconds
    DEFAULT_CDP_TIMEOUT = 30             # seconds

    # Browser defaults
    DEFAULT_VIEWPORT_WIDTH = 1920
    DEFAULT_VIEWPORT_HEIGHT = 1080
    DEFAULT_DEVICE_SCALE_FACTOR = 1.0

    # Performance monitoring
    DEFAULT_METRICS_INTERVAL = 1000      # milliseconds
    MAX_PERFORMANCE_ENTRIES = 1000

    # Security settings
    MAX_EXECUTION_TIME = 30              # seconds for JS execution
    MAX_RESPONSE_SIZE = 10 * 1024 * 1024 # 10MB max response


class HTTPStatus:
    """HTTP status codes used throughout the application"""

    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503


class ErrorMessages:
    """Standard error messages"""

    # CDP connection errors
    CDP_CONNECTION_FAILED = "Failed to connect to Chrome DevTools Protocol"
    CDP_TIMEOUT = "CDP operation timed out"
    CDP_INVALID_RESPONSE = "Invalid response from CDP"

    # DOM interaction errors
    ELEMENT_NOT_FOUND = "Element not found with given selector"
    ELEMENT_NOT_VISIBLE = "Element is not visible or interactable"
    INVALID_SELECTOR = "Invalid CSS selector provided"

    # Network errors
    NETWORK_REQUEST_FAILED = "Network request failed"
    INVALID_URL = "Invalid URL provided"

    # JavaScript execution errors
    JS_EXECUTION_FAILED = "JavaScript execution failed"
    JS_TIMEOUT = "JavaScript execution timed out"

    # File operation errors
    FILE_NOT_FOUND = "File not found"
    PERMISSION_DENIED = "Permission denied"

    # Generic errors
    INVALID_PARAMETERS = "Invalid parameters provided"
    OPERATION_FAILED = "Operation failed"
    INTERNAL_ERROR = "Internal server error"


class Endpoints:
    """API endpoint paths"""

    # Browser control
    NAVIGATE = "/browser/navigate"
    RELOAD = "/browser/reload"
    BACK = "/browser/back"
    FORWARD = "/browser/forward"

    # DOM interaction
    CLICK = "/dom/click"
    HOVER = "/dom/hover"
    DRAG = "/dom/drag"
    SCROLL = "/dom/scroll"

    # JavaScript execution
    EXECUTE_JS = "/js/execute"
    INJECT_JS = "/js/inject"

    # Network monitoring
    NETWORK_EVENTS = "/network/events"
    NETWORK_SIMULATE = "/network/simulate"

    # Performance monitoring
    PERFORMANCE_METRICS = "/performance/metrics"
    PERFORMANCE_TRACE = "/performance/trace"

    # Screenshot and capture
    SCREENSHOT = "/capture/screenshot"
    PDF = "/capture/pdf"

    # System utilities
    STATUS = "/system/status"
    HEALTH = "/system/health"


class NinjaSchools:
    """The Nine Schools of CDP Ninja"""

    HIDDEN_DOOR = "cdp-ninja-hidden-door"      # Togakure Ryū - Reconnaissance
    NINE_DEMONS = "cdp-ninja-nine-demons"      # Kuki Shinden Ryū - JavaScript mastery
    JEWEL_TIGER = "cdp-ninja-jewel-tiger"      # Gyokko Ryū - DOM precision
    JEWEL_HEART = "cdp-ninja-jewel-heart"      # Gyokushin Ryū - Network intelligence
    DIVINE_IMMOVABLE = "cdp-ninja-divine-immovable"  # Shinden Fudō Ryū - Error defense
    CLOUD_HIDING = "cdp-ninja-cloud-hiding"    # Kumogakure Ryū - Performance observation
    HIGH_TREE = "cdp-ninja-high-tree"          # Takagi Yōshin Ryū - Accessibility
    TIGER_KNOCKDOWN = "cdp-ninja-tiger-knockdown"  # Kotō Ryū - Stress testing
    RIGHTEOUS = "cdp-ninja-righteous"          # Gikan Ryū - Security guardian


class ConfigKeys:
    """Configuration setting keys"""

    # Server settings
    CDP_PORT = "cdp_port"
    BRIDGE_PORT = "bridge_port"
    BIND_HOST = "bind_host"
    DEBUG_MODE = "debug_mode"

    # Security settings
    SHELL_ENABLED = "shell_enabled"
    MAX_EVENTS = "max_events"
    RATE_LIMIT = "rate_limit"

    # Performance settings
    TIMEOUT = "timeout"
    POOL_SIZE = "pool_size"
    CACHE_SIZE = "cache_size"