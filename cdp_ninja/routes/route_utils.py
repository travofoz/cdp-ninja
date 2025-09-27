"""
Route Utilities - Common helpers for CDP ninja route modules
Provides domain management and common patterns for endpoint implementation
"""

import logging
from flask import jsonify
from typing import Dict, Any, Optional
from cdp_ninja.core.domain_manager import get_domain_manager, CDPDomain
from cdp_ninja.utils.error_reporter import crash_reporter

logger = logging.getLogger(__name__)


def ensure_domain_available(domain: CDPDomain, caller: str = "unknown") -> bool:
    """
    Ensure a CDP domain is available for use

    @param domain - The CDP domain to ensure
    @param caller - Identifier of the calling endpoint
    @returns True if domain is available
    """
    domain_manager = get_domain_manager()
    return domain_manager.ensure_domain(domain, caller)


def create_domain_error_response(domain: CDPDomain, caller: str = "unknown") -> tuple:
    """
    Create standardized error response for domain unavailability

    @param domain - The unavailable domain
    @param caller - The calling endpoint
    @returns Tuple of (json_response, status_code)
    """
    domain_manager = get_domain_manager()
    domain_status = domain_manager.get_domain_status()

    return jsonify({
        "success": False,
        "error": f"Required domain {domain.value} not available",
        "domain": domain.value,
        "caller": caller,
        "domain_risk_level": domain_manager.DOMAIN_CONFIGS.get(domain, {}).risk_level.value if domain_manager.DOMAIN_CONFIGS.get(domain) else "unknown",
        "max_risk_level": domain_status["max_risk_level"],
        "suggestion": f"Increase max risk level or use alternative implementation"
    }), 503


def create_success_response(data: Dict[str, Any], caller: str = "unknown",
                          domains_used: list = None) -> Dict[str, Any]:
    """
    Create standardized success response with domain usage tracking

    @param data - The response data
    @param caller - The calling endpoint
    @param domains_used - List of domains used in this operation
    @returns JSON response dictionary
    """
    response = {
        "success": True,
        **data
    }

    # Add domain usage info if provided
    if domains_used:
        response["domains_used"] = [d.value if isinstance(d, CDPDomain) else str(d) for d in domains_used]

    return response


def handle_cdp_error(operation: str, error: Exception, request_data: Dict[str, Any],
                    caller: str = "unknown") -> tuple:
    """
    Handle CDP operation errors with consistent error reporting

    @param operation - Name of the operation that failed
    @param error - The exception that occurred
    @param request_data - The request data that caused the error
    @param caller - The calling endpoint
    @returns Tuple of (json_response, status_code)
    """
    crash_data = crash_reporter.report_crash(
        operation=operation,
        error=error,
        request_data=request_data
    )

    return jsonify({
        "crash": True,
        "error": str(error),
        "operation": operation,
        "caller": caller,
        "crash_id": crash_data.get('timestamp')
    }), 500


def parse_request_params(request, param_names: list) -> Dict[str, Any]:
    """
    Parse request parameters from GET/POST with consistent handling

    @param request - Flask request object
    @param param_names - List of parameter names to extract
    @returns Dictionary of parsed parameters
    """
    if request.method == 'GET':
        return {name: request.args.get(name) for name in param_names}
    else:
        data = request.get_json() or {}
        return {name: data.get(name) for name in param_names}


def require_domains(domains: list):
    """
    Decorator to ensure required domains are available before endpoint execution

    @param domains - List of CDPDomain enums required
    @returns Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            caller = func.__name__

            # Check all required domains
            unavailable_domains = []
            for domain in domains:
                if not ensure_domain_available(domain, caller):
                    unavailable_domains.append(domain)

            # If any domains are unavailable, return error
            if unavailable_domains:
                return create_domain_error_response(unavailable_domains[0], caller)

            # All domains available, proceed with function
            return func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator


def get_domain_status_info() -> Dict[str, Any]:
    """
    Get current domain manager status for debugging

    @returns Domain status information
    """
    domain_manager = get_domain_manager()
    return domain_manager.get_domain_status()


def track_endpoint_usage(endpoint_name: str, domains_used: list = None,
                        request_data: Dict[str, Any] = None):
    """
    Track endpoint usage for analytics and optimization

    @param endpoint_name - Name of the endpoint
    @param domains_used - List of domains used
    @param request_data - Request parameters (sanitized)
    """
    # Update domain usage tracking
    if domains_used:
        for domain in domains_used:
            if isinstance(domain, CDPDomain):
                # This updates the last_used timestamp
                ensure_domain_available(domain, endpoint_name)

    # Log usage for analytics
    logger.debug(f"Endpoint usage: {endpoint_name}, domains: {domains_used}")


# Common domain groups for convenience
SAFE_DOMAINS = [
    CDPDomain.NETWORK,
    CDPDomain.RUNTIME,
    CDPDomain.PAGE,
    CDPDomain.DOM,
    CDPDomain.CONSOLE
]

PERFORMANCE_DOMAINS = [
    CDPDomain.PERFORMANCE,
    CDPDomain.MEMORY
]

SECURITY_DOMAINS = [
    CDPDomain.SECURITY,
    CDPDomain.NETWORK
]

ACCESSIBILITY_DOMAINS = [
    CDPDomain.ACCESSIBILITY,
    CDPDomain.DOM
]

PROFILING_DOMAINS = [
    CDPDomain.HEAPPROFILER,
    CDPDomain.PROFILER,
    CDPDomain.PERFORMANCE
]