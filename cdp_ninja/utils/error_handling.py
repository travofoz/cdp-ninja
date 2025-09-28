"""
CDP Error Handling Utilities
Standardized error response handling for CDP operations
"""

from flask import jsonify
from cdp_ninja.constants import HTTPStatus


def handle_cdp_error(result: dict, default_message: str = "CDP operation failed"):
    """Standard CDP error response handler"""
    if 'error' in result:
        return jsonify({
            "success": False,
            "error": result.get('error', default_message),
            "cdp_result": result
        }), HTTPStatus.INTERNAL_SERVER_ERROR
    return None