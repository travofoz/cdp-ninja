"""
Mouse Interaction Operations
Handles mouse movements, clicks, and drag operations via CDP
"""

from cdp_ninja.utils.error_handling import handle_cdp_error


def execute_mouse_drag(cdp_client, start_x: float, start_y: float, end_x: float, end_y: float):
    """Perform the actual mouse drag operation sequence

    Args:
        cdp_client: CDP client instance
        start_x: Starting X coordinate
        start_y: Starting Y coordinate
        end_x: Ending X coordinate
        end_y: Ending Y coordinate

    Returns:
        None if successful, error response tuple if failed
    """
    # 1. Mouse down at start position
    mouse_down = cdp_client.send_command('Input.dispatchMouseEvent', {
        'type': 'mousePressed',
        'x': start_x,
        'y': start_y,
        'button': 'left',
        'clickCount': 1
    })

    error_response = handle_cdp_error(mouse_down, "Mouse down operation failed")
    if error_response:
        return error_response

    # 2. Mouse move to end position (dragging)
    mouse_move = cdp_client.send_command('Input.dispatchMouseEvent', {
        'type': 'mouseMoved',
        'x': end_x,
        'y': end_y
    })

    error_response = handle_cdp_error(mouse_move, "Mouse move operation failed")
    if error_response:
        return error_response

    # 3. Mouse up at end position
    mouse_up = cdp_client.send_command('Input.dispatchMouseEvent', {
        'type': 'mouseReleased',
        'x': end_x,
        'y': end_y,
        'button': 'left'
    })

    error_response = handle_cdp_error(mouse_up, "Mouse up operation failed")
    if error_response:
        return error_response

    return None  # Success


def execute_mouse_click(cdp_client, x: float, y: float, button: str = 'left', click_count: int = 1):
    """Execute a mouse click at specified coordinates

    Args:
        cdp_client: CDP client instance
        x: X coordinate
        y: Y coordinate
        button: Mouse button ('left', 'right', 'middle')
        click_count: Number of clicks (1 for single, 2 for double)

    Returns:
        None if successful, error response tuple if failed
    """
    # Mouse press
    press_result = cdp_client.send_command('Input.dispatchMouseEvent', {
        'type': 'mousePressed',
        'x': x,
        'y': y,
        'button': button,
        'clickCount': click_count
    })

    error_response = handle_cdp_error(press_result, "Mouse press failed")
    if error_response:
        return error_response

    # Mouse release
    release_result = cdp_client.send_command('Input.dispatchMouseEvent', {
        'type': 'mouseReleased',
        'x': x,
        'y': y,
        'button': button
    })

    error_response = handle_cdp_error(release_result, "Mouse release failed")
    if error_response:
        return error_response

    return None  # Success


def execute_mouse_hover(cdp_client, x: float, y: float):
    """Execute a mouse hover at specified coordinates

    Args:
        cdp_client: CDP client instance
        x: X coordinate
        y: Y coordinate

    Returns:
        None if successful, error response tuple if failed
    """
    hover_result = cdp_client.send_command('Input.dispatchMouseEvent', {
        'type': 'mouseMoved',
        'x': x,
        'y': y
    })

    error_response = handle_cdp_error(hover_result, "Hover operation failed")
    if error_response:
        return error_response

    return None  # Success