"""
DOM Advanced Routes - Precision DOM manipulation and element analysis
Raw CDP commands for element analysis, positioning, and shadow DOM access
"""

import logging
from flask import Blueprint, jsonify, request
from cdp_ninja.core import get_global_pool
from cdp_ninja.utils.error_reporter import crash_reporter

logger = logging.getLogger(__name__)
dom_advanced_routes = Blueprint('dom_advanced', __name__)


def _resolve_node_id(cdp, selector, node_id=None):
    """
    Utility: Resolve element to node ID

    @param cdp - CDP connection
    @param selector - CSS selector
    @param node_id - Direct node ID (optional)
    @returns node_id or None if not found
    """
    if node_id:
        try:
            return int(node_id)
        except (ValueError, TypeError):
            return None

    if not selector:
        return None

    # Find node via Runtime.evaluate
    find_code = f"""
        (() => {{
            const el = document.querySelector('{selector}');
            return el ? el : null;
        }})()
    """

    eval_result = cdp.send_command('Runtime.evaluate', {
        'expression': find_code,
        'returnByValue': False
    })

    if 'result' in eval_result and 'objectId' in eval_result['result']:
        desc_result = cdp.send_command('DOM.describeNode', {
            'objectId': eval_result['result']['objectId']
        })

        if 'result' in desc_result and 'node' in desc_result['result']:
            return desc_result['result']['node']['nodeId']

    return None


def _parse_request_params(request, param_names):
    """
    Utility: Parse request parameters from GET/POST

    @param request - Flask request object
    @param param_names - List of parameter names to extract
    @returns dict of parameters
    """
    if request.method == 'GET':
        return {name: request.args.get(name) for name in param_names}
    else:
        data = request.get_json() or {}
        return {name: data.get(name) for name in param_names}


@dom_advanced_routes.route('/cdp/dom/get_bounds', methods=['GET', 'POST'])
def get_element_bounds():
    """
    Get element bounding box and positioning data

    @route GET/POST /cdp/dom/get_bounds
    @param {string} selector - Element selector
    @param {number} [nodeId] - Direct node ID (alternative to selector)
    @returns {object} Element bounds and positioning data

    @example
    // Get bounds by selector
    GET /cdp/dom/get_bounds?selector=#header

    // Get bounds by node ID
    POST {"nodeId": 42}

    // Malformed selector - test what breaks
    GET /cdp/dom/get_bounds?selector=>>>invalid<<<
    """
    try:
        params = _parse_request_params(request, ['selector', 'nodeId'])
        selector = params['selector'] or ''
        node_id = params['nodeId']

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            resolved_node_id = _resolve_node_id(cdp, selector, node_id)

            if resolved_node_id:
                # Get box model
                box_result = cdp.send_command('DOM.getBoxModel', {
                    'nodeId': resolved_node_id
                })

                return jsonify({
                    "success": 'error' not in box_result,
                    "selector": selector,
                    "nodeId": resolved_node_id,
                    "bounds": box_result.get('result', {}),
                    "cdp_result": box_result
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Element not found or no node ID provided",
                    "selector": selector,
                    "nodeId": node_id
                })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="get_element_bounds",
            error=e,
            request_data={'selector': selector, 'nodeId': node_id}
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "selector": selector,
            "crash_id": crash_data.get('timestamp')
        }), 500


@dom_advanced_routes.route('/cdp/dom/get_style', methods=['GET', 'POST'])
def get_computed_style():
    """
    Get computed style for element

    @route GET/POST /cdp/dom/get_style
    @param {string} selector - Element selector
    @param {number} [nodeId] - Direct node ID
    @param {array} [properties] - Specific CSS properties to get
    @returns {object} Computed style data

    @example
    // Get all computed styles
    GET /cdp/dom/get_style?selector=.container

    // Get specific properties
    POST {"selector": "#header", "properties": ["color", "font-size", "margin"]}

    // Malformed selector
    GET /cdp/dom/get_style?selector=>>>bad<<<
    """
    try:
        params = _parse_request_params(request, ['selector', 'nodeId'])
        selector = params['selector'] or ''
        node_id = params['nodeId']

        # Handle properties separately (array handling)
        if request.method == 'GET':
            properties = request.args.getlist('properties')
        else:
            data = request.get_json() or {}
            properties = data.get('properties', [])

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            resolved_node_id = _resolve_node_id(cdp, selector, node_id)

            if resolved_node_id:
                # Get computed style
                style_result = cdp.send_command('DOM.getComputedStyleForNode', {
                    'nodeId': resolved_node_id
                })

                computed_styles = {}
                if 'result' in style_result and 'computedStyle' in style_result['result']:
                    all_styles = style_result['result']['computedStyle']

                    if properties:
                        # Filter for requested properties
                        for style in all_styles:
                            if style['name'] in properties:
                                computed_styles[style['name']] = style['value']
                    else:
                        # Return all styles
                        for style in all_styles:
                            computed_styles[style['name']] = style['value']

                return jsonify({
                    "success": 'error' not in style_result,
                    "selector": selector,
                    "nodeId": resolved_node_id,
                    "properties": properties,
                    "computedStyle": computed_styles,
                    "cdp_result": style_result
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Element not found",
                    "selector": selector
                })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="get_computed_style",
            error=e,
            request_data={'selector': selector, 'nodeId': node_id, 'properties': properties}
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "selector": selector,
            "crash_id": crash_data.get('timestamp')
        }), 500


@dom_advanced_routes.route('/cdp/dom/is_visible', methods=['GET', 'POST'])
def check_element_visibility():
    """
    Check if element is visible (combines bounds + visibility calculation)

    @route GET/POST /cdp/dom/is_visible
    @param {string} selector - Element selector
    @param {number} [nodeId] - Direct node ID
    @param {boolean} [strict] - Strict visibility check (in viewport)
    @returns {object} Visibility analysis

    @example
    // Basic visibility check
    GET /cdp/dom/is_visible?selector=#popup

    // Strict viewport visibility
    POST {"selector": ".hidden-element", "strict": true}

    // Check multiple conditions
    GET /cdp/dom/is_visible?selector=div&strict=false
    """
    try:
        if request.method == 'GET':
            selector = request.args.get('selector', '')
            node_id = request.args.get('nodeId')
            strict = request.args.get('strict', 'false').lower() == 'true'
        else:
            data = request.get_json() or {}
            selector = data.get('selector', '')
            node_id = data.get('nodeId')
            strict = data.get('strict', False)

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Use JavaScript for comprehensive visibility check (no node ID needed)
            visibility_code = f"""
                (() => {{
                    const el = document.querySelector('{selector}');
                    if (!el) return null;

                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);

                    const checks = {{
                        element_exists: true,
                        has_dimensions: rect.width > 0 && rect.height > 0,
                        display_not_none: style.display !== 'none',
                        visibility_not_hidden: style.visibility !== 'hidden',
                        opacity_not_zero: parseFloat(style.opacity) > 0,
                        in_viewport: rect.top >= 0 && rect.left >= 0 &&
                                   rect.bottom <= window.innerHeight &&
                                   rect.right <= window.innerWidth,
                        not_clipped: style.overflow !== 'hidden' ||
                                   (rect.width <= el.scrollWidth && rect.height <= el.scrollHeight)
                    }};

                    // Calculate visibility score
                    const basicVisible = checks.has_dimensions &&
                                       checks.display_not_none &&
                                       checks.visibility_not_hidden &&
                                       checks.opacity_not_zero;

                    const strictVisible = basicVisible && checks.in_viewport;

                    return {{
                        ...checks,
                        basic_visible: basicVisible,
                        strict_visible: strictVisible,
                        is_visible: {'strictVisible' if strict else 'basicVisible'},
                        bounds: {{
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height,
                            top: rect.top,
                            right: rect.right,
                            bottom: rect.bottom,
                            left: rect.left
                        }},
                        computed_style: {{
                            display: style.display,
                            visibility: style.visibility,
                            opacity: style.opacity,
                            overflow: style.overflow,
                            position: style.position,
                            zIndex: style.zIndex
                        }}
                    }};
                }})()
            """

            result = cdp.send_command('Runtime.evaluate', {
                'expression': visibility_code,
                'returnByValue': True
            })

            visibility_data = result.get('result', {}).get('result', {}).get('value')

            return jsonify({
                "success": visibility_data is not None,
                "selector": selector,
                "strict_mode": strict,
                "visibility": visibility_data,
                "cdp_result": result
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="check_element_visibility",
            error=e,
            request_data={'selector': selector, 'nodeId': node_id, 'strict': strict}
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "selector": selector,
            "crash_id": crash_data.get('timestamp')
        }), 500


@dom_advanced_routes.route('/cdp/dom/shadow', methods=['GET', 'POST'])
def access_shadow_dom():
    """
    Access shadow DOM and describe shadow roots

    @route GET/POST /cdp/dom/shadow
    @param {string} selector - Host element selector
    @param {number} [nodeId] - Direct node ID
    @param {number} [depth] - Shadow tree depth
    @returns {object} Shadow DOM structure

    @example
    // Access shadow DOM
    GET /cdp/dom/shadow?selector=custom-element

    // Deep shadow tree
    POST {"selector": "#shadow-host", "depth": 3}

    // Test malformed selector
    GET /cdp/dom/shadow?selector=>>>invalid<<<
    """
    try:
        if request.method == 'GET':
            selector = request.args.get('selector', '')
            node_id = request.args.get('nodeId')
            depth = int(request.args.get('depth', 1))
        else:
            data = request.get_json() or {}
            selector = data.get('selector', '')
            node_id = data.get('nodeId')
            depth = data.get('depth', 1)

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Get node ID if we have selector
            if selector and not node_id:
                find_code = f"""
                    (() => {{
                        const el = document.querySelector('{selector}');
                        return el ? el : null;
                    }})()
                """

                eval_result = cdp.send_command('Runtime.evaluate', {
                    'expression': find_code,
                    'returnByValue': False
                })

                if 'result' in eval_result and 'objectId' in eval_result['result']:
                    desc_result = cdp.send_command('DOM.describeNode', {
                        'objectId': eval_result['result']['objectId'],
                        'depth': depth,
                        'pierce': True
                    })

                    return jsonify({
                        "success": 'error' not in desc_result,
                        "selector": selector,
                        "depth": depth,
                        "shadow_dom": desc_result.get('result', {}),
                        "cdp_result": desc_result
                    })

            elif node_id:
                try:
                    node_id = int(node_id)
                except (ValueError, TypeError):
                    pass

                desc_result = cdp.send_command('DOM.describeNode', {
                    'nodeId': node_id,
                    'depth': depth,
                    'pierce': True
                })

                return jsonify({
                    "success": 'error' not in desc_result,
                    "selector": selector,
                    "nodeId": node_id,
                    "depth": depth,
                    "shadow_dom": desc_result.get('result', {}),
                    "cdp_result": desc_result
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Element not found",
                    "selector": selector
                })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="access_shadow_dom",
            error=e,
            request_data={'selector': selector, 'nodeId': node_id, 'depth': depth}
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "selector": selector,
            "crash_id": crash_data.get('timestamp')
        }), 500


@dom_advanced_routes.route('/cdp/dom/parent', methods=['GET', 'POST'])
def get_parent_node():
    """
    Get parent node and navigation data

    @route GET/POST /cdp/dom/parent
    @param {string} selector - Element selector
    @param {number} [nodeId] - Direct node ID
    @param {boolean} [siblings] - Include sibling nodes
    @param {number} [levels] - Number of parent levels to traverse
    @returns {object} Parent node data and navigation info

    @example
    // Get immediate parent
    GET /cdp/dom/parent?selector=#child-element

    // Get parent with siblings
    POST {"selector": ".item", "siblings": true}

    // Traverse multiple parent levels
    GET /cdp/dom/parent?selector=span&levels=3
    """
    try:
        if request.method == 'GET':
            selector = request.args.get('selector', '')
            node_id = request.args.get('nodeId')
            include_siblings = request.args.get('siblings', 'false').lower() == 'true'
            levels = int(request.args.get('levels', 1))
        else:
            data = request.get_json() or {}
            selector = data.get('selector', '')
            node_id = data.get('nodeId')
            include_siblings = data.get('siblings', False)
            levels = data.get('levels', 1)

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # JavaScript approach for comprehensive parent navigation
            parent_code = f"""
                (() => {{
                    const el = document.querySelector('{selector}');
                    if (!el) return null;

                    const result = {{
                        original_element: {{
                            tagName: el.tagName,
                            id: el.id,
                            className: el.className
                        }},
                        parents: []
                    }};

                    let current = el.parentElement;
                    for (let i = 0; i < {levels} && current; i++) {{
                        const parent_info = {{
                            level: i + 1,
                            tagName: current.tagName,
                            id: current.id,
                            className: current.className,
                            childElementCount: current.childElementCount
                        }};

                        // Include siblings if requested
                        if ({str(include_siblings).lower()}) {{
                            parent_info.siblings = Array.from(current.children).map(child => ({{
                                tagName: child.tagName,
                                id: child.id,
                                className: child.className,
                                is_original: child === el
                            }}));
                        }}

                        result.parents.push(parent_info);
                        current = current.parentElement;
                    }}

                    return result;
                }})()
            """

            result = cdp.send_command('Runtime.evaluate', {
                'expression': parent_code,
                'returnByValue': True
            })

            parent_data = result.get('result', {}).get('result', {}).get('value')

            return jsonify({
                "success": parent_data is not None,
                "selector": selector,
                "levels": levels,
                "include_siblings": include_siblings,
                "navigation": parent_data,
                "cdp_result": result
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="get_parent_node",
            error=e,
            request_data={'selector': selector, 'nodeId': node_id, 'siblings': include_siblings, 'levels': levels}
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "selector": selector,
            "crash_id": crash_data.get('timestamp')
        }), 500