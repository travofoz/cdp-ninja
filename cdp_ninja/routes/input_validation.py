"""
Input Validation Utilities

Centralized validation functions for all endpoint parameters.
Prevents injection attacks and ensures type safety.
"""

import json
import re
from typing import Any, Optional, List, Dict
from urllib.parse import urlparse


class ValidationError(Exception):
    """Raised when validation fails"""
    pass


# Configuration
MAX_TEXT_INPUT_LENGTH = 100000
MAX_FORM_FIELDS = 100
MAX_ARRAY_SIZE = 100
MAX_SELECTOR_LENGTH = 500
MAX_URL_LENGTH = 2000
MAX_FIELD_VALUE_LENGTH = 50000
ALLOWED_URL_SCHEMES = ['http', 'https', 'about']


def validate_selector(selector: str, field_name: str = "selector") -> str:
    """
    Validate CSS selector for safety and reasonable length.

    @param selector - CSS selector string
    @param field_name - Name for error messages
    @returns Validated selector
    @raises ValidationError if invalid
    """
    if not isinstance(selector, str):
        raise ValidationError(f"{field_name} must be a string, got {type(selector).__name__}")

    if not selector:
        raise ValidationError(f"{field_name} cannot be empty")

    if len(selector) > MAX_SELECTOR_LENGTH:
        raise ValidationError(f"{field_name} too long (max {MAX_SELECTOR_LENGTH} chars)")

    return selector


def validate_coordinate(value: Any, name: str, max_val: int = 32767) -> int:
    """
    Validate and convert coordinate to integer.

    @param value - Coordinate value (string or number)
    @param name - Coordinate name for error messages (e.g., "x", "y")
    @param max_val - Maximum allowed value
    @returns Validated integer coordinate
    @raises ValidationError if invalid
    """
    try:
        coord = int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{name} must be an integer, got {value}")

    # Allow 0 and negative values for some cases, but cap them
    if coord < -32768:
        raise ValidationError(f"{name} too small (minimum -32768)")

    if coord > max_val:
        raise ValidationError(f"{name} too large (maximum {max_val})")

    return coord


def validate_coordinates(x: Any, y: Any, max_width: int = 32767, max_height: int = 32767) -> tuple:
    """
    Validate both X and Y coordinates.

    @param x - X coordinate
    @param y - Y coordinate
    @param max_width - Maximum X value
    @param max_height - Maximum Y value
    @returns Tuple of (validated_x, validated_y)
    @raises ValidationError if invalid
    """
    validated_x = validate_coordinate(x, "x", max_width)
    validated_y = validate_coordinate(y, "y", max_height)
    return (validated_x, validated_y)


def validate_text_input(text: str, field_name: str = "text", max_length: int = MAX_TEXT_INPUT_LENGTH) -> str:
    """
    Validate text input for length and type.

    @param text - Text input
    @param field_name - Name for error messages
    @param max_length - Maximum allowed length
    @returns Validated text
    @raises ValidationError if invalid
    """
    if not isinstance(text, str):
        raise ValidationError(f"{field_name} must be a string, got {type(text).__name__}")

    if len(text) > max_length:
        raise ValidationError(f"{field_name} too long (max {max_length} characters)")

    return text


def validate_url(url: str, allow_javascript: bool = False, allow_data: bool = False) -> str:
    """
    Validate URL for safe navigation.

    @param url - URL to validate
    @param allow_javascript - Allow javascript: URLs (default False)
    @param allow_data - Allow data: URLs (default False)
    @returns Validated URL
    @raises ValidationError if invalid
    """
    if not isinstance(url, str):
        raise ValidationError(f"URL must be a string, got {type(url).__name__}")

    if not url:
        raise ValidationError("URL cannot be empty")

    if len(url) > MAX_URL_LENGTH:
        raise ValidationError(f"URL too long (max {MAX_URL_LENGTH} characters)")

    # Parse URL
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
    except Exception as e:
        raise ValidationError(f"Invalid URL format: {e}")

    # Check scheme allowlist
    allowed = list(ALLOWED_URL_SCHEMES)
    if allow_javascript:
        allowed.append('javascript')
    if allow_data:
        allowed.append('data')

    if scheme and scheme not in allowed:
        raise ValidationError(f"URL scheme '{scheme}' not allowed. Allowed: {allowed}")

    # Special case: about:blank is always safe
    if url.lower() == 'about:blank':
        return url

    return url


def validate_integer_param(value: Any, name: str, default: int = None,
                          min_val: Optional[int] = None,
                          max_val: Optional[int] = None) -> int:
    """
    Validate and convert parameter to integer with bounds checking.

    @param value - Parameter value
    @param name - Parameter name for error messages
    @param default - Default value if None
    @param min_val - Minimum allowed value
    @param max_val - Maximum allowed value
    @returns Validated integer
    @raises ValidationError if invalid
    """
    if value is None:
        if default is None:
            raise ValidationError(f"{name} is required")
        return default

    try:
        result = int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{name} must be an integer, got {value}")

    if min_val is not None and result < min_val:
        raise ValidationError(f"{name} must be >= {min_val}, got {result}")

    if max_val is not None and result > max_val:
        raise ValidationError(f"{name} must be <= {max_val}, got {result}")

    return result


def validate_boolean_param(value: Any, name: str = "boolean", default: bool = False) -> bool:
    """
    Validate and convert parameter to boolean.

    @param value - Parameter value
    @param name - Parameter name for error messages
    @param default - Default value if None
    @returns Validated boolean
    """
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.lower() in ['true', '1', 'yes', 'on']

    if isinstance(value, int):
        return value != 0

    return default


def validate_form_fields(fields: Dict[str, Any],
                        max_fields: int = MAX_FORM_FIELDS,
                        max_value_length: int = MAX_FIELD_VALUE_LENGTH) -> Dict[str, str]:
    """
    Validate form fields dictionary.

    @param fields - Dictionary of field selectors to values
    @param max_fields - Maximum number of fields allowed
    @param max_value_length - Maximum length of field values
    @returns Validated fields dictionary
    @raises ValidationError if invalid
    """
    if not isinstance(fields, dict):
        raise ValidationError(f"fields must be a dictionary, got {type(fields).__name__}")

    if len(fields) > max_fields:
        raise ValidationError(f"Too many fields ({len(fields)}), max {max_fields}")

    validated = {}
    for selector, value in fields.items():
        # Validate selector
        validate_selector(selector, f"field selector '{selector}'")

        # Validate value
        value_str = str(value) if not isinstance(value, str) else value
        if len(value_str) > max_value_length:
            raise ValidationError(f"Field value too long for '{selector}' (max {max_value_length})")

        validated[selector] = value_str

    return validated


def validate_array_param(values: Any, name: str = "array",
                        max_size: int = MAX_ARRAY_SIZE,
                        item_validator=None) -> List[Any]:
    """
    Validate array/list parameter.

    @param values - Array/list to validate
    @param name - Parameter name for error messages
    @param max_size - Maximum array size
    @param item_validator - Optional validation function for each item
    @returns Validated array
    @raises ValidationError if invalid
    """
    if not isinstance(values, (list, tuple)):
        raise ValidationError(f"{name} must be a list/array, got {type(values).__name__}")

    if len(values) > max_size:
        raise ValidationError(f"{name} too large ({len(values)} items), max {max_size}")

    if item_validator:
        return [item_validator(item) for item in values]

    return list(values)


# DEPRECATED: escape_javascript_string() is no longer used
# Use javascript_safe_value() instead for safe JSON encoding


def javascript_safe_value(value: Any) -> str:
    """
    Convert a Python value to a safe JavaScript literal.

    Uses JSON encoding for maximum safety. This prevents injection attacks
    by ensuring values are properly quoted and escaped.

    @param value - Python value to convert
    @returns JSON-encoded string safe for use in JavaScript
    """
    return json.dumps(value)


def validate_css_property_name(prop: str) -> str:
    """
    Validate CSS property name.

    @param prop - CSS property name
    @returns Validated property name
    @raises ValidationError if invalid
    """
    if not isinstance(prop, str):
        raise ValidationError(f"CSS property must be a string, got {type(prop).__name__}")

    # Allow alphanumeric, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9\-_]+$', prop):
        raise ValidationError(f"Invalid CSS property name: {prop}")

    return prop


def validate_css_property_value(value: str) -> str:
    """
    Validate CSS property value (basic validation).

    @param value - CSS property value
    @returns Validated value
    @raises ValidationError if invalid
    """
    if not isinstance(value, str):
        raise ValidationError(f"CSS value must be a string, got {type(value).__name__}")

    if len(value) > 1000:
        raise ValidationError("CSS value too long (max 1000 characters)")

    # Reject common injection patterns
    if any(pattern in value.lower() for pattern in ['javascript:', 'expression(', 'import']):
        raise ValidationError("CSS value contains forbidden content")

    return value


def validate_attributes(attributes: Dict[str, str]) -> Dict[str, str]:
    """
    Validate HTML attributes dictionary.

    @param attributes - Dictionary of attribute names to values
    @returns Validated attributes
    @raises ValidationError if invalid
    """
    if not isinstance(attributes, dict):
        raise ValidationError(f"attributes must be a dictionary, got {type(attributes).__name__}")

    # Dangerous attributes that should be blocked
    dangerous_attributes = {
        'onload', 'onerror', 'onmouseover', 'onmouseout', 'onclick', 'onchange',
        'onsubmit', 'onfocus', 'onblur', 'ondblclick', 'onkeydown', 'onkeyup',
        'onkeypress', 'onmousedown', 'onmouseup', 'onwheel', 'onscroll',
        'ontouchstart', 'ontouchend', 'ontouchmove', 'ondragstart', 'ondrop'
    }

    validated = {}
    for name, value in attributes.items():
        if not isinstance(name, str):
            raise ValidationError(f"Attribute name must be string, got {type(name).__name__}")
        if not isinstance(value, str):
            raise ValidationError(f"Attribute value must be string, got {type(value).__name__}")

        # Reject dangerous event handler attributes
        if name.lower() in dangerous_attributes or name.lower().startswith('on'):
            raise ValidationError(f"Event attribute '{name}' not allowed")

        # Reject dangerous protocol-based attributes
        if name.lower() in ['href', 'src', 'data', 'formaction', 'poster', 'srcset']:
            if any(pattern in value.lower() for pattern in ['javascript:', 'data:text', 'vbscript:']):
                raise ValidationError(f"Attribute value '{name}' contains forbidden protocol")

        # Validate other attribute values don't contain dangerous content
        if any(pattern in value.lower() for pattern in ['javascript:', 'vbscript:', 'expression(']):
            raise ValidationError(f"Attribute value contains forbidden content")

        validated[name] = value

    return validated


def validate_depth(depth: Any, max_depth: int = 10) -> int:
    """
    Validate DOM tree depth parameter.

    @param depth - Depth value (can be -1 for unlimited)
    @param max_depth - Maximum depth if not unlimited
    @returns Validated depth
    @raises ValidationError if invalid
    """
    try:
        d = int(depth)
    except (ValueError, TypeError):
        raise ValidationError(f"depth must be integer, got {depth}")

    if d == -1:
        return -1  # -1 means unlimited

    if d < 0 or d > max_depth:
        raise ValidationError(f"depth must be -1 (unlimited) or 0-{max_depth}, got {d}")

    return d


def validate_timeout(timeout: Any, max_timeout: int = 600000) -> int:
    """
    Validate timeout parameter in milliseconds.

    @param timeout - Timeout value in milliseconds
    @param max_timeout - Maximum allowed timeout
    @returns Validated timeout
    @raises ValidationError if invalid
    """
    try:
        t = int(timeout)
    except (ValueError, TypeError):
        raise ValidationError(f"timeout must be integer, got {timeout}")

    if t < 0:
        raise ValidationError(f"timeout cannot be negative, got {t}")

    if t > max_timeout:
        raise ValidationError(f"timeout too large (max {max_timeout}ms), got {t}")

    return t
