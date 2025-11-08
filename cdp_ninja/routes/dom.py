"""
DOM Routes - DOM manipulation and form operations with input validation
Safe DOM querying, modification, and form handling
"""

import logging
from flask import Blueprint, jsonify, request
from cdp_ninja.core.cdp_pool import get_global_pool
from cdp_ninja.utils.error_reporter import crash_reporter
from cdp_ninja.routes.input_validation import (
    validate_selector, validate_text_input, validate_boolean_param,
    validate_integer_param, validate_depth, validate_form_fields,
    validate_attributes, validate_css_property_name, validate_css_property_value,
    validate_array_param, javascript_safe_value, ValidationError
)

logger = logging.getLogger(__name__)
dom_routes = Blueprint('dom', __name__)


@dom_routes.route('/cdp/dom/snapshot', methods=['GET'])
def get_dom_snapshot():
    """
    Get current DOM tree snapshot

    @route GET /cdp/dom/snapshot
    @param {number} [depth] - DOM tree depth (-1 for full tree, max 10)
    @param {boolean} [include_text] - Include text nodes (default: false)
    @returns {object} DOM tree or HTML content

    @example
    // Full DOM tree
    GET /cdp/dom/snapshot?depth=-1

    // Limited depth
    GET /cdp/dom/snapshot?depth=3

    // Include text nodes
    GET /cdp/dom/snapshot?include_text=true
    """
    try:
        depth = validate_depth(request.args.get('depth', 1))
        include_text = validate_boolean_param(request.args.get('include_text', False))

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Get DOM document
            doc_result = cdp.send_command('DOM.getDocument', {
                'depth': depth,
                'pierce': True
            })

            if 'result' in doc_result and 'root' in doc_result['result']:
                root_id = doc_result['result']['root']['nodeId']

                # Get outer HTML for easier reading
                html_result = cdp.send_command('DOM.getOuterHTML', {
                    'nodeId': root_id
                })

                return jsonify({
                    "success": True,
                    "dom_tree": doc_result['result'],
                    "html": html_result.get('result', {}).get('outerHTML', ''),
                    "depth": depth,
                    "include_text": include_text
                })
            else:
                return jsonify(doc_result)

        finally:
            pool.release(cdp)

    except ValidationError as e:
        return jsonify({"error": str(e), "validation_failed": True}), 400

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="get_dom_snapshot",
            error=e,
            request_data={'depth': request.args.get('depth'), 'include_text': request.args.get('include_text')}
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "error_type": type(e).__name__,
            "crash_id": crash_data.get('timestamp')
        }), 500


@dom_routes.route('/cdp/dom/query', methods=['POST'])
def query_selector():
    """
    Query DOM elements

    @route POST /cdp/dom/query
    @param {string} selector - CSS selector to query
    @param {boolean} [all] - Return all matches (default: false)
    @param {boolean} [details] - Include element details (default: false)
    @returns {object} Query results

    @example
    // Single element
    {"selector": "div.container"}

    // Multiple elements
    {"selector": "input[type='text']", "all": true}

    // With details
    {"selector": "button.submit", "details": true}
    """
    try:
        data = request.get_json() or {}
        selector = validate_selector(data.get('selector', ''))
        query_all = validate_boolean_param(data.get('all', False))
        include_details = validate_boolean_param(data.get('details', False))

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Use JavaScript to query with safe selector
            if query_all:
                code = f"""
                    (() => {{
                        const elements = document.querySelectorAll({javascript_safe_value(selector)});
                        return Array.from(elements).map(el => ({{
                            tagName: el.tagName,
                            id: el.id,
                            className: el.className,
                            textContent: el.textContent ? el.textContent.substring(0, 200) : ''
                        }}));
                    }})()
                """
            else:
                code = f"""
                    (() => {{
                        const el = document.querySelector({javascript_safe_value(selector)});
                        if (!el) return null;
                        return {{
                            tagName: el.tagName,
                            id: el.id,
                            className: el.className,
                            textContent: el.textContent ? el.textContent.substring(0, 200) : '',
                            innerHTML: el.innerHTML ? el.innerHTML.substring(0, 500) : '',
                            outerHTML: el.outerHTML ? el.outerHTML.substring(0, 1000) : ''
                        }};
                    }})()
                """

            if include_details:
                code = code.replace(
                    'textContent: el.textContent',
                    '''textContent: el.textContent ? el.textContent.substring(0, 200) : '',
                    attributes: Array.from(el.attributes).reduce((acc, attr) => {
                        acc[attr.name] = attr.value;
                        return acc;
                    }, {}),
                    boundingRect: el.getBoundingClientRect(),
                    style: window.getComputedStyle(el).cssText'''
                )

            result = cdp.send_command('Runtime.evaluate', {
                'expression': code,
                'returnByValue': True
            })

            return jsonify({
                "success": 'error' not in result,
                "selector": selector,
                "query_all": query_all,
                "include_details": include_details,
                "elements": result.get('result', {}).get('result', {}).get('value')
            })

        finally:
            pool.release(cdp)

    except ValidationError as e:
        return jsonify({"error": str(e), "validation_failed": True}), 400

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="query_selector",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "error_type": type(e).__name__,
            "selector": data.get('selector'),
            "crash_id": crash_data.get('timestamp')
        }), 500


@dom_routes.route('/cdp/form/fill', methods=['POST'])
def fill_form():
    """
    Fill form fields with validated selectors and values

    @route POST /cdp/form/fill
    @param {object} fields - Object mapping selectors to values
    @param {boolean} [trigger_events] - Trigger input/change events
    @returns {object} Fill results for each field

    @example
    // Normal form fill
    {"fields": {"#email": "test@example.com", "#password": "secret"}}

    // Malformed selectors and values
    {"fields": {">>>bad<<<": "test\0null\nbytes", "#other": ""}}

    // Huge values - test limits
    {"fields": {"#input": "A".repeat(1000000)}}

    // Special characters
    {"fields": {"#text": "\\n\\t\\r\\0\\u0000"}}
    """
    try:
        data = request.get_json() or {}
        fields = validate_form_fields(data.get('fields', {}))
        trigger_events = validate_boolean_param(data.get('trigger_events', True))

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            results = []

            for selector, value in fields.items():
                try:
                    # Fill field with validated selector and value
                    events_code = ""
                    if trigger_events:
                        events_code = """
                            el.dispatchEvent(new Event('input', {bubbles: true}));
                            el.dispatchEvent(new Event('change', {bubbles: true}));
                            el.dispatchEvent(new Event('blur', {bubbles: true}));
                        """

                    code = f"""
                        (() => {{
                            const el = document.querySelector({javascript_safe_value(selector)});
                            if (el) {{
                                el.value = {javascript_safe_value(value)};
                                el.focus();
                                {events_code}
                                return true;
                            }}
                            return false;
                        }})()
                    """

                    result = cdp.send_command('Runtime.evaluate', {
                        'expression': code,
                        'returnByValue': True
                    })

                    success = result.get('result', {}).get('result', {}).get('value', False)

                    results.append({
                        "field": selector,
                        "value": value,
                        "value_length": len(str(value)),
                        "success": success,
                        "cdp_result": result if not success else None
                    })

                except Exception as field_error:
                    results.append({
                        "field": selector,
                        "value": value,
                        "success": False,
                        "error": str(field_error)
                    })

            return jsonify({
                "success": True,
                "filled_fields": results,
                "total_fields": len(fields),
                "successful_fields": sum(1 for r in results if r["success"])
            })

        finally:
            pool.release(cdp)

    except ValidationError as e:
        return jsonify({"error": str(e), "validation_failed": True}), 400

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="fill_form",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "fields": list(data.get('fields', {}).keys()),
            "crash_id": crash_data.get('timestamp')
        }), 500


@dom_routes.route('/cdp/form/submit', methods=['POST'])
def submit_form():
    """
    Submit form by selector with validated method

    @route POST /cdp/form/submit
    @param {string} selector - Form selector
    @param {string} [method] - Submit method (submit/click/enter, default: submit)
    @returns {object} Submit result

    @example
    // Normal form submit
    {"selector": "#login-form"}

    // Submit via button click
    {"selector": "#submit-btn", "method": "click"}

    // Submit via enter key
    {"selector": "#form", "method": "enter"}

    // Malformed selector
    {"selector": ">>>invalid<<<"}
    """
    try:
        data = request.get_json() or {}
        selector = validate_selector(data.get('selector', ''))
        method = data.get('method', 'submit').lower()

        # Whitelist allowed methods to prevent arbitrary property access
        allowed_methods = ['submit', 'click', 'enter']
        if method not in allowed_methods:
            raise ValidationError(f"method must be one of: {', '.join(allowed_methods)}, got '{method}'")

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            if method == 'submit':
                code = f"document.querySelector({javascript_safe_value(selector)}).submit()"
            elif method == 'click':
                code = f"document.querySelector({javascript_safe_value(selector)}).click()"
            elif method == 'enter':
                code = f"""
                    (() => {{
                        const el = document.querySelector({javascript_safe_value(selector)});
                        el.focus();
                        el.dispatchEvent(new KeyboardEvent('keydown', {{key: 'Enter', code: 'Enter'}}));
                        el.dispatchEvent(new KeyboardEvent('keyup', {{key: 'Enter', code: 'Enter'}}));
                        return 'enter_sent';
                    }})()
                """

            result = cdp.send_command('Runtime.evaluate', {
                'expression': code,
                'returnByValue': True
            })

            return jsonify({
                "success": 'error' not in result,
                "selector": selector,
                "method": method,
                "cdp_result": result
            })

        finally:
            pool.release(cdp)

    except ValidationError as e:
        return jsonify({"error": str(e), "validation_failed": True}), 400

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="submit_form",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "selector": data.get('selector'),
            "method": data.get('method'),
            "crash_id": crash_data.get('timestamp')
        }), 500


@dom_routes.route('/cdp/form/values', methods=['POST'])
def get_form_values():
    """
    Get current form field values with validated selectors

    @route POST /cdp/form/values
    @param {array} selectors - Array of field selectors
    @param {string} [form_selector] - Get all inputs from a form
    @returns {object} Current field values

    @example
    // Get specific fields
    {"selectors": ["#email", "#password", "#username"]}

    // Get all form inputs
    {"form_selector": "#login-form"}

    // Malformed selectors
    {"selectors": [">>>bad<<<", "#normal"]}
    """
    try:
        data = request.get_json() or {}
        raw_selectors = data.get('selectors', [])
        raw_form_selector = data.get('form_selector')

        # Validate selectors if provided
        selectors = []
        if raw_selectors:
            selectors = validate_array_param(raw_selectors, "selectors", item_validator=validate_selector)

        form_selector = None
        if raw_form_selector:
            form_selector = validate_selector(raw_form_selector, "form_selector")

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            values = {}

            if form_selector:
                # Get all inputs from form with validated selector
                code = f"""
                    (() => {{
                        const form = document.querySelector({javascript_safe_value(form_selector)});
                        if (!form) return {{}};

                        const inputs = form.querySelectorAll('input, select, textarea');
                        const values = {{}};

                        inputs.forEach(input => {{
                            if (input.name) {{
                                values[input.name] = input.value;
                            }} else if (input.id) {{
                                values['#' + input.id] = input.value;
                            }}
                        }});

                        return values;
                    }})()
                """

                result = cdp.send_command('Runtime.evaluate', {
                    'expression': code,
                    'returnByValue': True
                })

                if 'result' in result:
                    values = result['result'].get('result', {}).get('value', {})

            else:
                # Get individual field values with validated selectors
                for selector in selectors:
                    try:
                        code = f"""
                            (() => {{
                                const el = document.querySelector({javascript_safe_value(selector)});
                                return el ? el.value : null;
                            }})()
                        """

                        result = cdp.send_command('Runtime.evaluate', {
                            'expression': code,
                            'returnByValue': True
                        })

                        values[selector] = result.get('result', {}).get('result', {}).get('value')

                    except Exception as field_error:
                        values[selector] = {"error": str(field_error)}

            return jsonify({
                "success": True,
                "values": values,
                "form_selector": form_selector,
                "field_selectors": selectors
            })

        finally:
            pool.release(cdp)

    except ValidationError as e:
        return jsonify({"error": str(e), "validation_failed": True}), 400

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="get_form_values",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "crash_id": crash_data.get('timestamp')
        }), 500


@dom_routes.route('/cdp/dom/modify', methods=['POST'])
def modify_dom():
    """
    Modify DOM elements with validated inputs

    @route POST /cdp/dom/modify
    @param {string} selector - Element selector
    @param {string} [action] - Modification action (html, text, attr, style, remove)
    @param {string} [content] - New content (for html/text)
    @param {object} [attributes] - Attributes to set
    @param {object} [styles] - Styles to apply
    @returns {object} Modification result

    @example
    // Change HTML content
    {"selector": "#content", "action": "html", "content": "<h1>Modified</h1>"}

    // Inject script - test XSS
    {"selector": "body", "action": "html", "content": "<script>alert('injected')</script>"}

    // Remove element
    {"selector": "#unwanted", "action": "remove"}

    // Set dangerous attributes
    {"selector": "img", "attributes": {"src": "javascript:alert('xss')"}}
    """
    try:
        data = request.get_json() or {}
        selector = validate_selector(data.get('selector', ''))
        action = data.get('action', 'html').lower()
        # Support both 'content' and 'value' parameters
        content = data.get('content', data.get('value', ''))

        # Validate content as text input if provided
        if content:
            content = validate_text_input(content, "content")

        # Validate attributes if provided
        raw_attributes = data.get('attributes', {})
        attributes = {}
        if raw_attributes:
            attributes = validate_attributes(raw_attributes)

        # Validate styles if provided
        raw_styles = data.get('styles', {})
        styles = {}
        if raw_styles:
            if not isinstance(raw_styles, dict):
                raise ValidationError("styles must be a dictionary")
            for prop, value in raw_styles.items():
                validated_prop = validate_css_property_name(prop)
                validated_value = validate_css_property_value(str(value) if not isinstance(value, str) else value)
                styles[validated_prop] = validated_value

        # Normalize action aliases
        action_aliases = {
            'set_text': 'text',
            'set_html': 'html',
            'set_content': 'text'
        }
        action = action_aliases.get(action, action)

        # Whitelist allowed actions to prevent arbitrary property assignment
        allowed_actions = ['html', 'text', 'attr', 'style', 'remove']
        if action not in allowed_actions:
            raise ValidationError(f"action must be one of: {', '.join(allowed_actions)}, got '{action}'")

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            if action == 'html':
                code = f"""
                    (() => {{
                        const el = document.querySelector({javascript_safe_value(selector)});
                        if (el) {{
                            el.innerHTML = {javascript_safe_value(content)};
                            return 'html_set';
                        }}
                        return 'element_not_found';
                    }})()
                """
            elif action == 'text':
                code = f"""
                    (() => {{
                        const el = document.querySelector({javascript_safe_value(selector)});
                        if (el) {{
                            el.textContent = {javascript_safe_value(content)};
                            return 'text_set';
                        }}
                        return 'element_not_found';
                    }})()
                """
            elif action == 'remove':
                code = f"""
                    (() => {{
                        const el = document.querySelector({javascript_safe_value(selector)});
                        if (el) {{
                            el.remove();
                            return 'element_removed';
                        }}
                        return 'element_not_found';
                    }})()
                """
            elif action == 'attr':
                attr_code = []
                for attr, value in attributes.items():
                    attr_code.append(f"el.setAttribute({javascript_safe_value(attr)}, {javascript_safe_value(value)})")
                code = f"""
                    (() => {{
                        const el = document.querySelector({javascript_safe_value(selector)});
                        if (el) {{
                            {'; '.join(attr_code)}
                            return 'attributes_set';
                        }}
                        return 'element_not_found';
                    }})()
                """
            elif action == 'style':
                style_code = []
                for prop, value in styles.items():
                    # Style property names need camelCase conversion
                    style_code.append(f"el.style.{prop} = {javascript_safe_value(value)}")
                code = f"""
                    (() => {{
                        const el = document.querySelector({javascript_safe_value(selector)});
                        if (el) {{
                            {'; '.join(style_code)}
                            return 'styles_applied';
                        }}
                        return 'element_not_found';
                    }})()
                """

            result = cdp.send_command('Runtime.evaluate', {
                'expression': code,
                'returnByValue': True
            })

            return jsonify({
                "success": 'error' not in result,
                "selector": selector,
                "action": action,
                "content": content,
                "attributes": attributes,
                "styles": styles,
                "cdp_result": result
            })

        finally:
            pool.release(cdp)

    except ValidationError as e:
        return jsonify({"error": str(e), "validation_failed": True}), 400

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="modify_dom",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "modification_params": data,
            "crash_id": crash_data.get('timestamp')
        }), 500