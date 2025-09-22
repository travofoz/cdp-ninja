"""
DOM Routes - RAW DOM manipulation and form operations
No validation, no sanitization - test all edge cases
"""

import logging
from flask import Blueprint, jsonify, request
from cdp_ninja.core import get_global_pool
from cdp_ninja.utils.error_reporter import crash_reporter

logger = logging.getLogger(__name__)
dom_routes = Blueprint('dom', __name__)


@dom_routes.route('/cdp/dom/snapshot', methods=['GET'])
def get_dom_snapshot():
    """
    Get current DOM tree snapshot

    @route GET /cdp/dom/snapshot
    @param {number} [depth] - DOM tree depth (-1 for full tree)
    @param {boolean} [include_text] - Include text nodes
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
        depth = request.args.get('depth', 1)
        include_text = request.args.get('include_text', 'false').lower() == 'true'

        # Convert depth to int if possible
        try:
            depth = int(depth)
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid depth parameter '{depth}': {e}")
            depth = 1

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

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="get_dom_snapshot",
            error=e,
            request_data={'depth': request.args.get('depth'), 'include_text': request.args.get('include_text')}
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "crash_id": crash_data.get('timestamp')
        }), 500


@dom_routes.route('/cdp/dom/query', methods=['POST'])
def query_selector():
    """
    Query DOM with ANY selector - malformed selectors welcome

    @route POST /cdp/dom/query
    @param {string} selector - ANY CSS selector
    @param {boolean} [all] - Return all matches (querySelectorAll)
    @param {boolean} [details] - Include element details
    @returns {object} Query results or crash data

    @example
    // Normal query
    {"selector": "div.container"}

    // Malformed selector - see what happens
    {"selector": ">>>invalid<<<"}

    // Complex selector - test limits
    {"selector": "div > span:nth-child(999999999999)"}

    // Injection attempt
    {"selector": "div'; alert('xss'); //"}
    """
    try:
        data = request.get_json() or {}
        selector = data.get('selector', '')  # Could be anything
        query_all = data.get('all', False)
        include_details = data.get('details', False)

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            # Use JavaScript to query - RAW selector, no escaping
            if query_all:
                code = f"""
                    (() => {{
                        const elements = document.querySelectorAll('{selector}');
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
                        const el = document.querySelector('{selector}');
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
                "elements": result.get('result', {}).get('result', {}).get('value'),
                "cdp_result": result
            })

        finally:
            pool.release(cdp)

    except Exception as e:
        crash_data = crash_reporter.report_crash(
            operation="query_selector",
            error=e,
            request_data=data
        )

        return jsonify({
            "crash": True,
            "error": str(e),
            "selector": data.get('selector'),
            "crash_id": crash_data.get('timestamp')
        }), 500


@dom_routes.route('/cdp/form/fill', methods=['POST'])
def fill_form():
    """
    Fill form fields - ANY selectors, ANY values

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
        fields = data.get('fields', {})  # No validation of selectors or values
        trigger_events = data.get('trigger_events', True)

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            results = []

            for selector, value in fields.items():
                try:
                    # Fill field with RAW value - no escaping
                    events_code = ""
                    if trigger_events:
                        events_code = """
                            el.dispatchEvent(new Event('input', {bubbles: true}));
                            el.dispatchEvent(new Event('change', {bubbles: true}));
                            el.dispatchEvent(new Event('blur', {bubbles: true}));
                        """

                    code = f"""
                        (() => {{
                            const el = document.querySelector('{selector}');
                            if (el) {{
                                el.value = '{value}';
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
    Submit form by selector

    @route POST /cdp/form/submit
    @param {string} selector - Form selector (no validation)
    @param {string} [method] - Submit method (submit/click/enter)
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
        selector = data.get('selector', '')  # No validation
        method = data.get('method', 'submit')  # submit, click, enter

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            if method == 'submit':
                code = f"document.querySelector('{selector}').submit()"
            elif method == 'click':
                code = f"document.querySelector('{selector}').click()"
            elif method == 'enter':
                code = f"""
                    (() => {{
                        const el = document.querySelector('{selector}');
                        el.focus();
                        el.dispatchEvent(new KeyboardEvent('keydown', {{key: 'Enter', code: 'Enter'}}));
                        el.dispatchEvent(new KeyboardEvent('keyup', {{key: 'Enter', code: 'Enter'}}));
                        return 'enter_sent';
                    }})()
                """
            else:
                # Unknown method - try it anyway
                code = f"document.querySelector('{selector}').{method}()"

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
    Get current form field values

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
        selectors = data.get('selectors', [])
        form_selector = data.get('form_selector')

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            values = {}

            if form_selector:
                # Get all inputs from form
                code = f"""
                    (() => {{
                        const form = document.querySelector('{form_selector}');
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
                # Get individual field values
                for selector in selectors:
                    try:
                        code = f"""
                            (() => {{
                                const el = document.querySelector('{selector}');
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
    Modify DOM elements - ANY changes allowed

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
        selector = data.get('selector', '')
        action = data.get('action', 'html')
        content = data.get('content', '')
        attributes = data.get('attributes', {})
        styles = data.get('styles', {})

        pool = get_global_pool()
        cdp = pool.acquire()

        try:
            if action == 'html':
                code = f"document.querySelector('{selector}').innerHTML = '{content}'"
            elif action == 'text':
                code = f"document.querySelector('{selector}').textContent = '{content}'"
            elif action == 'remove':
                code = f"document.querySelector('{selector}').remove()"
            elif action == 'attr':
                attr_code = []
                for attr, value in attributes.items():
                    attr_code.append(f"el.setAttribute('{attr}', '{value}')")
                code = f"""
                    (() => {{
                        const el = document.querySelector('{selector}');
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
                    style_code.append(f"el.style.{prop} = '{value}'")
                code = f"""
                    (() => {{
                        const el = document.querySelector('{selector}');
                        if (el) {{
                            {'; '.join(style_code)}
                            return 'styles_applied';
                        }}
                        return 'element_not_found';
                    }})()
                """
            else:
                # Unknown action - try it as property
                code = f"document.querySelector('{selector}').{action} = '{content}'"

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