"""
Coordinate Processing for Security Testing
Handles coordinate extraction for user interactions
⚠️ NO VALIDATION - Allows malformed coordinates for fuzzing
"""

from typing import Tuple, Any


def validate_drag_coordinates(data: dict) -> Tuple[Any, Any, Any, Any]:
    """Extract drag coordinates from request data - NO VALIDATION for security testing

    ⚠️ WARNING: This function allows NaN, Infinity, strings, and any malformed
    input to pass through for security testing and browser fuzzing.

    Args:
        data: Request data containing startX, startY, endX, endY

    Returns:
        Tuple of (start_x, start_y, end_x, end_y) - raw values, no conversion
    """
    # Return raw values for security testing - no validation or conversion
    return data['startX'], data['startY'], data['endX'], data['endY']


def validate_point_coordinates(data: dict) -> Tuple[Any, Any]:
    """Extract point coordinates from request data - NO VALIDATION for security testing

    ⚠️ WARNING: This function allows NaN, Infinity, strings, and any malformed
    input to pass through for security testing and browser fuzzing.

    Args:
        data: Request data containing x, y coordinates

    Returns:
        Tuple of (x, y) - raw values, no conversion
    """
    # Return raw values for security testing - no validation or conversion
    return data['x'], data['y']