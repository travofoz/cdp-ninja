"""
DOM Element Coordinate Operations
Handles getting coordinates from DOM elements via CDP
"""

from typing import Tuple
from cdp_ninja.templates.javascript import JSTemplates


def get_element_coordinates(cdp_client, selector: str, element_type: str = "element") -> Tuple[float, float]:
    """Get center coordinates of DOM element

    Args:
        cdp_client: CDP client instance
        selector: CSS selector for the target element
        element_type: Description of element type for error messages

    Returns:
        Tuple of (x, y) center coordinates as floats

    Raises:
        RuntimeError: If element cannot be found or evaluated
    """
    code = JSTemplates.get_element_center_coordinates(selector)
    result = cdp_client.send_command('Runtime.evaluate', {
        'expression': code,
        'returnByValue': True
    })

    if 'result' not in result or 'result' not in result['result']:
        raise RuntimeError(f"Failed to evaluate {element_type} selector")

    coords = result['result']['result']
    if not coords:
        raise RuntimeError(f"{element_type.capitalize()} not found")

    return coords['x'], coords['y']


def get_element_bounds(cdp_client, selector: str) -> dict:
    """Get full bounding rectangle of DOM element

    Args:
        cdp_client: CDP client instance
        selector: CSS selector for the target element

    Returns:
        Dictionary with x, y, width, height, top, left, bottom, right

    Raises:
        RuntimeError: If element cannot be found or evaluated
    """
    code = JSTemplates.get_element_bounds(selector)
    result = cdp_client.send_command('Runtime.evaluate', {
        'expression': code,
        'returnByValue': True
    })

    if 'result' not in result or 'result' not in result['result']:
        raise RuntimeError("Failed to evaluate element bounds")

    bounds = result['result']['result']
    if not bounds:
        raise RuntimeError("Element not found")

    return bounds