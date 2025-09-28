"""
CDP Ninja User Interaction Module
Handles mouse, keyboard, and coordinate operations
"""

from .coordinates import validate_drag_coordinates, validate_point_coordinates
from .mouse import execute_mouse_drag, execute_mouse_click, execute_mouse_hover

__all__ = [
    'validate_drag_coordinates',
    'validate_point_coordinates',
    'execute_mouse_drag',
    'execute_mouse_click',
    'execute_mouse_hover'
]