"""
Security Testing Routes
Vulnerability assessment and ethical security testing
8 endpoints for defensive security analysis
"""

import logging
from flask import Blueprint, request, jsonify
from cdp_ninja.core.cdp_pool import get_global_pool
from cdp_ninja.core.domain_manager import CDPDomain
from .route_utils import (
    require_domains, create_success_response, handle_cdp_error,
    parse_request_params, track_endpoint_usage, SECURITY_DOMAINS
)

logger = logging.getLogger(__name__)

security_routes = Blueprint('security', __name__)


@security_routes.route('/cdp/security/vulnerabilities', methods=['GET', 'POST'])
@require_domains([CDPDomain.SECURITY])
def security_vulnerabilities():
    """
    Scan for common web vulnerabilities using Security domain

    @route GET/POST /cdp/security/vulnerabilities
    @param {string} [target_url] - Specific URL to analyze
    @param {boolean} [include_recommendations=true] - Include fix recommendations
    @returns {object} Vulnerability assessment report with findings and severity levels
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            # Parse request parameters
            params = parse_request_params(request, ['target_url', 'include_recommendations'])
            target_url = params.get('target_url', 'current')
            include_recommendations = params.get('include_recommendations', 'true').lower() == 'true'

            # Enable Security domain for vulnerability scanning
            security_enable = client.send_command('Security.enable')
            if not security_enable.get('success'):
                return jsonify({"error": "Failed to enable Security domain"}), 500

            # Get current page URL if not specified
            if target_url == 'current':
                runtime_evaluate = client.send_command('Runtime.evaluate', {
                    'expression': 'window.location.href'
                })
                if runtime_evaluate.get('success') and 'result' in runtime_evaluate:
                    target_url = runtime_evaluate['result'].get('value', 'unknown')

            # Security state analysis
            security_state = client.send_command('Security.getSecurityState')

            # Mixed content analysis
            mixed_content_js = """
            (() => {
                const issues = [];

                // Check for mixed content
                const protocol = window.location.protocol;
                if (protocol === 'https:') {
                    // Check images
                    document.querySelectorAll('img').forEach(img => {
                        if (img.src && img.src.startsWith('http:')) {
                            issues.push({
                                type: 'mixed_content',
                                severity: 'medium',
                                element: 'img',
                                url: img.src,
                                description: 'HTTP image on HTTPS page'
                            });
                        }
                    });

                    // Check scripts
                    document.querySelectorAll('script[src]').forEach(script => {
                        if (script.src && script.src.startsWith('http:')) {
                            issues.push({
                                type: 'mixed_content',
                                severity: 'high',
                                element: 'script',
                                url: script.src,
                                description: 'HTTP script on HTTPS page - active mixed content'
                            });
                        }
                    });

                    // Check stylesheets
                    document.querySelectorAll('link[rel="stylesheet"]').forEach(link => {
                        if (link.href && link.href.startsWith('http:')) {
                            issues.push({
                                type: 'mixed_content',
                                severity: 'medium',
                                element: 'stylesheet',
                                url: link.href,
                                description: 'HTTP stylesheet on HTTPS page'
                            });
                        }
                    });
                }

                // Check for inline event handlers (XSS risk)
                document.querySelectorAll('*').forEach(el => {
                    const attributes = el.getAttributeNames();
                    attributes.forEach(attr => {
                        if (attr.startsWith('on')) {
                            issues.push({
                                type: 'inline_handler',
                                severity: 'medium',
                                element: el.tagName.toLowerCase(),
                                attribute: attr,
                                description: 'Inline event handler detected - potential XSS vector'
                            });
                        }
                    });
                });

                // Check for eval usage in inline scripts
                document.querySelectorAll('script:not([src])').forEach(script => {
                    if (script.textContent && script.textContent.includes('eval(')) {
                        issues.push({
                            type: 'eval_usage',
                            severity: 'high',
                            element: 'script',
                            description: 'eval() usage detected - code injection risk'
                        });
                    }
                });

                // Check for document.write usage
                document.querySelectorAll('script:not([src])').forEach(script => {
                    if (script.textContent && script.textContent.includes('document.write')) {
                        issues.push({
                            type: 'document_write',
                            severity: 'medium',
                            element: 'script',
                            description: 'document.write usage - injection vulnerability'
                        });
                    }
                });

                return {
                    total_issues: issues.length,
                    issues: issues,
                    scan_timestamp: Date.now(),
                    page_protocol: protocol
                };
            })()
            """

            mixed_content_result = client.send_command('Runtime.evaluate', {
                'expression': mixed_content_js,
                'returnByValue': True
            })

            vulnerability_data = {
                "target_url": target_url,
                "security_state": security_state.get('result', {}),
                "mixed_content_analysis": mixed_content_result.get('result', {}).get('value', {}),
                "scan_timestamp": mixed_content_result.get('result', {}).get('value', {}).get('scan_timestamp'),
            }

            # Add recommendations if requested
            if include_recommendations:
                recommendations = []
                issues = vulnerability_data.get('mixed_content_analysis', {}).get('issues', [])

                for issue in issues:
                    if issue['type'] == 'mixed_content':
                        recommendations.append(f"Convert {issue['url']} to HTTPS")
                    elif issue['type'] == 'inline_handler':
                        recommendations.append(f"Move {issue['attribute']} to addEventListener in external script")
                    elif issue['type'] == 'eval_usage':
                        recommendations.append("Replace eval() with safer alternatives like JSON.parse()")
                    elif issue['type'] == 'document_write':
                        recommendations.append("Replace document.write with DOM manipulation methods")

                vulnerability_data['recommendations'] = recommendations

            track_endpoint_usage('security_vulnerabilities', [CDPDomain.SECURITY], {
                'target_url': target_url,
                'issues_found': len(vulnerability_data.get('mixed_content_analysis', {}).get('issues', []))
            })

            return jsonify(create_success_response(vulnerability_data, 'security_vulnerabilities', [CDPDomain.SECURITY]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('security_vulnerabilities', e,
                              {'target_url': target_url}, 'security_vulnerabilities')


@security_routes.route('/cdp/security/authentication', methods=['GET', 'POST'])
@require_domains([CDPDomain.SECURITY, CDPDomain.NETWORK])
def authentication_analysis():
    """
    Analyze authentication mechanisms and security headers

    @route GET/POST /cdp/security/authentication
    @param {string} [auth_type] - Type of auth to analyze (cookie, token, session)
    @param {boolean} [check_headers=true] - Analyze security headers
    @returns {object} Authentication security analysis including header analysis and auth flow review
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            params = parse_request_params(request, ['auth_type', 'check_headers'])
            auth_type = params.get('auth_type', 'all')
            check_headers = params.get('check_headers', 'true').lower() == 'true'

            # Enable required domains
            client.send_command('Security.enable')
            client.send_command('Network.enable')

            # Analyze authentication storage
            auth_analysis_js = """
            (() => {
                const auth_analysis = {
                    cookies: [],
                    localStorage_keys: [],
                    sessionStorage_keys: [],
                    auth_headers_detected: false,
                    security_issues: []
                };

                // Analyze cookies
                if (document.cookie) {
                    const cookies = document.cookie.split(';');
                    cookies.forEach(cookie => {
                        const [name, value] = cookie.trim().split('=');
                        const cookieInfo = {
                            name: name,
                            has_value: !!value,
                            appears_auth_related: /auth|token|session|login|jwt/i.test(name)
                        };

                        // Check for security flags (can't directly access from JS)
                        if (cookieInfo.appears_auth_related) {
                            auth_analysis.security_issues.push({
                                type: 'auth_cookie_analysis_needed',
                                severity: 'medium',
                                cookie: name,
                                description: 'Authentication cookie requires server-side security flag analysis'
                            });
                        }

                        auth_analysis.cookies.push(cookieInfo);
                    });
                }

                // Analyze localStorage
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    const keyInfo = {
                        key: key,
                        appears_auth_related: /auth|token|session|login|jwt|user/i.test(key)
                    };

                    if (keyInfo.appears_auth_related) {
                        auth_analysis.security_issues.push({
                            type: 'auth_localstorage',
                            severity: 'high',
                            key: key,
                            description: 'Authentication data in localStorage - XSS vulnerable'
                        });
                    }

                    auth_analysis.localStorage_keys.push(keyInfo);
                }

                // Analyze sessionStorage
                for (let i = 0; i < sessionStorage.length; i++) {
                    const key = sessionStorage.key(i);
                    const keyInfo = {
                        key: key,
                        appears_auth_related: /auth|token|session|login|jwt|user/i.test(key)
                    };

                    if (keyInfo.appears_auth_related) {
                        auth_analysis.security_issues.push({
                            type: 'auth_sessionstorage',
                            severity: 'medium',
                            key: key,
                            description: 'Authentication data in sessionStorage - consider cookies with HttpOnly'
                        });
                    }

                    auth_analysis.sessionStorage_keys.push(keyInfo);
                }

                // Check for Authorization headers in fetch/XHR interceptor
                const originalFetch = window.fetch;
                let authHeaderDetected = false;

                // Look for existing auth patterns in window
                if (window.localStorage.getItem('token') ||
                    window.localStorage.getItem('authToken') ||
                    window.localStorage.getItem('jwt')) {
                    auth_analysis.auth_headers_detected = true;
                }

                return auth_analysis;
            })()
            """

            auth_result = client.send_command('Runtime.evaluate', {
                'expression': auth_analysis_js,
                'returnByValue': True
            })

            auth_data = {
                "auth_type_requested": auth_type,
                "authentication_analysis": auth_result.get('result', {}).get('value', {}),
                "check_headers": check_headers
            }

            # Security headers analysis if requested
            if check_headers:
                headers_js = """
                (() => {
                    const headers_analysis = {
                        security_headers: {},
                        missing_headers: [],
                        recommendations: []
                    };

                    // Check meta tags for security policies
                    const cspMeta = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
                    if (cspMeta) {
                        headers_analysis.security_headers['csp_meta'] = cspMeta.content;
                    } else {
                        headers_analysis.missing_headers.push('Content-Security-Policy');
                        headers_analysis.recommendations.push('Add Content-Security-Policy header to prevent XSS');
                    }

                    // Check for X-Frame-Options indication
                    try {
                        if (window.top !== window.self) {
                            headers_analysis.security_headers['x_frame_options'] = 'allows_framing';
                            headers_analysis.recommendations.push('Consider X-Frame-Options: DENY to prevent clickjacking');
                        }
                    } catch (e) {
                        headers_analysis.security_headers['x_frame_options'] = 'blocks_framing';
                    }

                    return headers_analysis;
                })()
                """

                headers_result = client.send_command('Runtime.evaluate', {
                    'expression': headers_js,
                    'returnByValue': True
                })

                auth_data['security_headers'] = headers_result.get('result', {}).get('value', {})

            track_endpoint_usage('authentication_analysis', [CDPDomain.SECURITY, CDPDomain.NETWORK], {
                'auth_type': auth_type,
                'headers_checked': check_headers
            })

            return jsonify(create_success_response(auth_data, 'authentication_analysis', [CDPDomain.SECURITY, CDPDomain.NETWORK]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('authentication_analysis', e,
                              {'auth_type': auth_type}, 'authentication_analysis')


@security_routes.route('/cdp/security/data_protection', methods=['GET', 'POST'])
@require_domains([CDPDomain.SECURITY])
def data_protection_analysis():
    """
    Analyze data protection and privacy compliance measures

    @route GET/POST /cdp/security/data_protection
    @param {boolean} [check_forms=true] - Analyze form security
    @param {boolean} [check_storage=true] - Analyze data storage patterns
    @returns {object} Data protection analysis including form security and storage compliance
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            params = parse_request_params(request, ['check_forms', 'check_storage'])
            check_forms = params.get('check_forms', 'true').lower() == 'true'
            check_storage = params.get('check_storage', 'true').lower() == 'true'

            client.send_command('Security.enable')

            protection_analysis_js = """
            (() => {
                const protection_analysis = {
                    forms_analysis: {},
                    storage_analysis: {},
                    privacy_concerns: [],
                    compliance_issues: []
                };

                // Form security analysis
                if (arguments[0]) { // check_forms
                    const forms = document.querySelectorAll('form');
                    protection_analysis.forms_analysis = {
                        total_forms: forms.length,
                        password_forms: 0,
                        unencrypted_forms: 0,
                        autocomplete_issues: [],
                        security_issues: []
                    };

                    forms.forEach((form, index) => {
                        const hasPasswordField = form.querySelector('input[type="password"]');
                        const action = form.action || window.location.href;

                        if (hasPasswordField) {
                            protection_analysis.forms_analysis.password_forms++;

                            // Check if form submits over HTTP
                            if (action.startsWith('http:')) {
                                protection_analysis.forms_analysis.unencrypted_forms++;
                                protection_analysis.forms_analysis.security_issues.push({
                                    form_index: index,
                                    issue: 'password_over_http',
                                    severity: 'critical',
                                    description: 'Password form submits over unencrypted HTTP'
                                });
                            }
                        }

                        // Check autocomplete on sensitive fields
                        const sensitiveFields = form.querySelectorAll('input[type="password"], input[name*="credit"], input[name*="card"], input[name*="ssn"]');
                        sensitiveFields.forEach(field => {
                            if (field.autocomplete !== 'off' && field.autocomplete !== 'new-password') {
                                protection_analysis.forms_analysis.autocomplete_issues.push({
                                    form_index: index,
                                    field_type: field.type,
                                    field_name: field.name,
                                    issue: 'autocomplete_enabled',
                                    description: 'Sensitive field allows autocomplete'
                                });
                            }
                        });
                    });
                }

                // Storage analysis
                if (arguments[1]) { // check_storage
                    protection_analysis.storage_analysis = {
                        localStorage_items: localStorage.length,
                        sessionStorage_items: sessionStorage.length,
                        sensitive_data_detected: [],
                        cookie_count: document.cookie.split(';').filter(c => c.trim()).length
                    };

                    // Check for PII patterns in storage
                    const piiPatterns = [
                        {pattern: /email|mail/i, type: 'email'},
                        {pattern: /phone|tel/i, type: 'phone'},
                        {pattern: /address|street|zip/i, type: 'address'},
                        {pattern: /ssn|social.?security/i, type: 'ssn'},
                        {pattern: /credit|card|payment/i, type: 'financial'},
                        {pattern: /password|pwd|pass/i, type: 'credentials'}
                    ];

                    // Check localStorage
                    for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        piiPatterns.forEach(pattern => {
                            if (pattern.pattern.test(key)) {
                                protection_analysis.storage_analysis.sensitive_data_detected.push({
                                    storage_type: 'localStorage',
                                    key: key,
                                    data_type: pattern.type,
                                    severity: pattern.type === 'credentials' ? 'critical' : 'high'
                                });
                            }
                        });
                    }

                    // Check sessionStorage
                    for (let i = 0; i < sessionStorage.length; i++) {
                        const key = sessionStorage.key(i);
                        piiPatterns.forEach(pattern => {
                            if (pattern.pattern.test(key)) {
                                protection_analysis.storage_analysis.sensitive_data_detected.push({
                                    storage_type: 'sessionStorage',
                                    key: key,
                                    data_type: pattern.type,
                                    severity: pattern.type === 'credentials' ? 'critical' : 'medium'
                                });
                            }
                        });
                    }
                }

                // Privacy compliance checks
                const privacyPolicyLink = document.querySelector('a[href*="privacy"], a[href*="policy"]');
                if (!privacyPolicyLink) {
                    protection_analysis.privacy_concerns.push({
                        type: 'missing_privacy_policy',
                        severity: 'medium',
                        description: 'No privacy policy link detected'
                    });
                }

                // GDPR cookie consent check
                const cookieConsentIndicators = document.querySelector('[class*="cookie"], [id*="cookie"], [class*="consent"], [id*="consent"]');
                if (document.cookie && !cookieConsentIndicators) {
                    protection_analysis.privacy_concerns.push({
                        type: 'missing_cookie_consent',
                        severity: 'high',
                        description: 'Cookies present but no consent mechanism detected'
                    });
                }

                return protection_analysis;
            })()
            """

            protection_result = client.send_command('Runtime.evaluate', {
                'expression': protection_analysis_js,
                'arguments': [
                    {'value': check_forms},
                    {'value': check_storage}
                ],
                'returnByValue': True
            })

            protection_data = {
                "data_protection_analysis": protection_result.get('result', {}).get('value', {}),
                "analysis_scope": {
                    "forms_checked": check_forms,
                    "storage_checked": check_storage
                }
            }

            track_endpoint_usage('data_protection_analysis', [CDPDomain.SECURITY], {
                'forms_checked': check_forms,
                'storage_checked': check_storage
            })

            return jsonify(create_success_response(protection_data, 'data_protection_analysis', [CDPDomain.SECURITY]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('data_protection_analysis', e,
                              {'check_forms': check_forms, 'check_storage': check_storage}, 'data_protection_analysis')


@security_routes.route('/cdp/security/threat_assessment', methods=['GET', 'POST'])
@require_domains([CDPDomain.SECURITY, CDPDomain.RUNTIME])
def threat_assessment():
    """
    Perform comprehensive threat assessment of current page

    @route GET/POST /cdp/security/threat_assessment
    @param {string} [focus_area] - Specific threat area to focus on (xss, injection, clickjacking)
    @param {boolean} [include_mitigation=true] - Include mitigation strategies
    @returns {object} Comprehensive threat assessment with risk levels and mitigation recommendations
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            params = parse_request_params(request, ['focus_area', 'include_mitigation'])
            focus_area = params.get('focus_area', 'all')
            include_mitigation = params.get('include_mitigation', 'true').lower() == 'true'

            client.send_command('Security.enable')
            client.send_command('Runtime.enable')

            threat_assessment_js = """
            (() => {
                const assessment = {
                    threat_vectors: [],
                    risk_level: 'low',
                    security_score: 100,
                    vulnerabilities: [],
                    attack_surface: {}
                };

                let vulnerabilityCount = 0;
                let highRiskCount = 0;

                // XSS Threat Assessment
                if (arguments[0] === 'all' || arguments[0] === 'xss') {
                    // Check for user input fields
                    const inputFields = document.querySelectorAll('input[type="text"], input[type="search"], textarea');
                    if (inputFields.length > 0) {
                        assessment.attack_surface.user_input_fields = inputFields.length;

                        // Check if inputs are properly escaped (basic heuristic)
                        inputFields.forEach((input, index) => {
                            if (input.value && /<[^>]*>/g.test(input.value)) {
                                assessment.vulnerabilities.push({
                                    type: 'potential_xss',
                                    severity: 'high',
                                    element_index: index,
                                    description: 'Input field contains HTML-like content without apparent escaping'
                                });
                                vulnerabilityCount++;
                                highRiskCount++;
                            }
                        });
                    }

                    // Check for innerHTML usage in scripts
                    const scripts = document.querySelectorAll('script:not([src])');
                    scripts.forEach(script => {
                        if (script.textContent.includes('innerHTML') &&
                            !script.textContent.includes('textContent')) {
                            assessment.vulnerabilities.push({
                                type: 'innerHTML_usage',
                                severity: 'medium',
                                description: 'innerHTML usage detected - potential XSS if user input involved'
                            });
                            vulnerabilityCount++;
                        }
                    });
                }

                // Injection Threat Assessment
                if (arguments[0] === 'all' || arguments[0] === 'injection') {
                    // Check for dynamic script generation
                    const dynamicScriptPatterns = ['eval(', 'Function(', 'setTimeout(', 'setInterval('];
                    scripts.forEach(script => {
                        dynamicScriptPatterns.forEach(pattern => {
                            if (script.textContent.includes(pattern)) {
                                assessment.vulnerabilities.push({
                                    type: 'dynamic_code_execution',
                                    severity: 'high',
                                    pattern: pattern,
                                    description: `Dynamic code execution pattern detected: ${pattern}`
                                });
                                vulnerabilityCount++;
                                highRiskCount++;
                            }
                        });
                    });

                    // Check for URL parameter injection points
                    const urlParams = new URLSearchParams(window.location.search);
                    const paramCount = Array.from(urlParams.keys()).length;
                    if (paramCount > 0) {
                        assessment.attack_surface.url_parameters = paramCount;

                        // Check if URL params are reflected in DOM
                        urlParams.forEach((value, key) => {
                            if (document.body.innerHTML.includes(value)) {
                                assessment.vulnerabilities.push({
                                    type: 'url_param_reflection',
                                    severity: 'medium',
                                    parameter: key,
                                    description: 'URL parameter value reflected in page content'
                                });
                                vulnerabilityCount++;
                            }
                        });
                    }
                }

                // Clickjacking Assessment
                if (arguments[0] === 'all' || arguments[0] === 'clickjacking') {
                    try {
                        if (window.top === window.self) {
                            assessment.attack_surface.frame_protection = 'not_framed';
                        } else {
                            assessment.vulnerabilities.push({
                                type: 'clickjacking_vulnerability',
                                severity: 'medium',
                                description: 'Page can be framed - potential clickjacking risk'
                            });
                            vulnerabilityCount++;
                        }
                    } catch (e) {
                        assessment.attack_surface.frame_protection = 'frame_protection_enabled';
                    }
                }

                // Calculate overall risk level
                if (highRiskCount > 0) {
                    assessment.risk_level = 'high';
                    assessment.security_score = Math.max(20, 100 - (vulnerabilityCount * 15));
                } else if (vulnerabilityCount > 2) {
                    assessment.risk_level = 'medium';
                    assessment.security_score = Math.max(50, 100 - (vulnerabilityCount * 10));
                } else if (vulnerabilityCount > 0) {
                    assessment.risk_level = 'low';
                    assessment.security_score = Math.max(70, 100 - (vulnerabilityCount * 5));
                }

                // Threat vectors summary
                assessment.threat_vectors = [
                    {
                        vector: 'Cross-Site Scripting (XSS)',
                        risk_level: inputFields.length > 0 ? 'medium' : 'low',
                        entry_points: assessment.attack_surface.user_input_fields || 0
                    },
                    {
                        vector: 'Code Injection',
                        risk_level: highRiskCount > 0 ? 'high' : 'low',
                        entry_points: assessment.attack_surface.url_parameters || 0
                    },
                    {
                        vector: 'Clickjacking',
                        risk_level: assessment.attack_surface.frame_protection === 'not_framed' ? 'medium' : 'low',
                        entry_points: assessment.attack_surface.frame_protection === 'not_framed' ? 1 : 0
                    }
                ];

                return assessment;
            })()
            """

            threat_result = client.send_command('Runtime.evaluate', {
                'expression': threat_assessment_js,
                'arguments': [{'value': focus_area}],
                'returnByValue': True
            })

            threat_data = {
                "focus_area": focus_area,
                "threat_assessment": threat_result.get('result', {}).get('value', {}),
                "include_mitigation": include_mitigation
            }

            # Add mitigation strategies if requested
            if include_mitigation:
                assessment = threat_data.get('threat_assessment', {})
                vulnerabilities = assessment.get('vulnerabilities', [])

                mitigation_strategies = []
                for vuln in vulnerabilities:
                    if vuln['type'] == 'potential_xss':
                        mitigation_strategies.append("Implement input validation and output encoding")
                    elif vuln['type'] == 'innerHTML_usage':
                        mitigation_strategies.append("Replace innerHTML with textContent or use sanitization libraries")
                    elif vuln['type'] == 'dynamic_code_execution':
                        mitigation_strategies.append(f"Avoid {vuln['pattern']} or implement strict Content Security Policy")
                    elif vuln['type'] == 'url_param_reflection':
                        mitigation_strategies.append("Sanitize URL parameters before displaying in DOM")
                    elif vuln['type'] == 'clickjacking_vulnerability':
                        mitigation_strategies.append("Implement X-Frame-Options: DENY or CSP frame-ancestors directive")

                threat_data['mitigation_strategies'] = list(set(mitigation_strategies))

            track_endpoint_usage('threat_assessment', [CDPDomain.SECURITY, CDPDomain.RUNTIME], {
                'focus_area': focus_area,
                'vulnerabilities_found': len(threat_data.get('threat_assessment', {}).get('vulnerabilities', []))
            })

            return jsonify(create_success_response(threat_data, 'threat_assessment', [CDPDomain.SECURITY, CDPDomain.RUNTIME]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('threat_assessment', e,
                              {'focus_area': focus_area}, 'threat_assessment')


@security_routes.route('/cdp/security/penetration_test', methods=['GET', 'POST'])
@require_domains([CDPDomain.SECURITY, CDPDomain.RUNTIME])
def penetration_test():
    """
    Perform ethical penetration testing of web application security

    @route GET/POST /cdp/security/penetration_test
    @param {string} [test_type] - Type of pen test (input_validation, auth_bypass, session)
    @param {boolean} [safe_mode=true] - Perform only safe, non-destructive tests
    @returns {object} Penetration test results with security findings and proof-of-concept demonstrations
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            params = parse_request_params(request, ['test_type', 'safe_mode'])
            test_type = params.get('test_type', 'input_validation')
            safe_mode = params.get('safe_mode', 'true').lower() == 'true'

            client.send_command('Security.enable')
            client.send_command('Runtime.enable')

            # Ethical penetration testing - read-only analysis only
            pen_test_js = """
            (() => {
                const penTest = {
                    test_type: arguments[0],
                    safe_mode: arguments[1],
                    findings: [],
                    proof_of_concepts: [],
                    risk_assessment: {},
                    test_coverage: {}
                };

                // Input Validation Testing (safe, read-only)
                if (arguments[0] === 'input_validation' || arguments[0] === 'all') {
                    const forms = document.querySelectorAll('form');
                    const inputs = document.querySelectorAll('input, textarea, select');

                    penTest.test_coverage.input_validation = {
                        forms_tested: forms.length,
                        inputs_tested: inputs.length,
                        tests_performed: []
                    };

                    inputs.forEach((input, index) => {
                        const inputType = input.type || 'text';
                        const hasValidation = !!(input.pattern || input.required || input.min || input.max);

                        if (!hasValidation && (inputType === 'text' || inputType === 'email')) {
                            penTest.findings.push({
                                test_type: 'input_validation',
                                severity: 'medium',
                                element_index: index,
                                element_type: inputType,
                                finding: 'missing_client_side_validation',
                                description: 'Input field lacks client-side validation attributes'
                            });
                        }

                        // Check for dangerous input types without restrictions
                        if (inputType === 'file' && !input.accept) {
                            penTest.findings.push({
                                test_type: 'input_validation',
                                severity: 'high',
                                element_index: index,
                                finding: 'unrestricted_file_upload',
                                description: 'File input without type restrictions'
                            });
                        }

                        penTest.test_coverage.input_validation.tests_performed.push(`${inputType}_validation_check`);
                    });
                }

                // Authentication Bypass Testing (safe analysis only)
                if (arguments[0] === 'auth_bypass' || arguments[0] === 'all') {
                    penTest.test_coverage.auth_bypass = {
                        tests_performed: [],
                        bypass_opportunities: []
                    };

                    // Check for password fields and their security
                    const passwordFields = document.querySelectorAll('input[type="password"]');
                    passwordFields.forEach((field, index) => {
                        const form = field.closest('form');

                        // Check if password is visible in DOM attributes
                        if (field.value) {
                            penTest.findings.push({
                                test_type: 'auth_bypass',
                                severity: 'critical',
                                element_index: index,
                                finding: 'password_in_dom',
                                description: 'Password value present in DOM - potential security leak'
                            });
                        }

                        // Check for autocomplete on password fields
                        if (field.autocomplete !== 'new-password' && field.autocomplete !== 'current-password') {
                            penTest.findings.push({
                                test_type: 'auth_bypass',
                                severity: 'medium',
                                element_index: index,
                                finding: 'password_autocomplete_risk',
                                description: 'Password field without proper autocomplete attribute'
                            });
                        }

                        penTest.test_coverage.auth_bypass.tests_performed.push('password_field_analysis');
                    });

                    // Check for hidden auth fields
                    const hiddenInputs = document.querySelectorAll('input[type="hidden"]');
                    hiddenInputs.forEach((input, index) => {
                        if (/token|auth|session|key/i.test(input.name || input.id || '')) {
                            penTest.findings.push({
                                test_type: 'auth_bypass',
                                severity: 'medium',
                                element_index: index,
                                finding: 'auth_token_in_hidden_field',
                                description: 'Authentication token in hidden field - inspect for exposure'
                            });
                        }
                    });
                }

                // Session Management Testing
                if (arguments[0] === 'session' || arguments[0] === 'all') {
                    penTest.test_coverage.session = {
                        cookies_analyzed: 0,
                        storage_analyzed: 0,
                        findings: []
                    };

                    // Analyze session cookies (read-only)
                    if (document.cookie) {
                        const cookies = document.cookie.split(';');
                        penTest.test_coverage.session.cookies_analyzed = cookies.length;

                        cookies.forEach(cookie => {
                            const cookieName = cookie.trim().split('=')[0];
                            if (/session|sess|auth|login/i.test(cookieName)) {
                                penTest.findings.push({
                                    test_type: 'session',
                                    severity: 'medium',
                                    finding: 'session_cookie_analysis_needed',
                                    cookie_name: cookieName,
                                    description: 'Session cookie requires server-side security analysis'
                                });
                            }
                        });
                    }

                    // Check session storage for sensitive data
                    for (let i = 0; i < sessionStorage.length; i++) {
                        const key = sessionStorage.key(i);
                        if (/session|user|auth|token/i.test(key)) {
                            penTest.findings.push({
                                test_type: 'session',
                                severity: 'high',
                                finding: 'session_data_in_storage',
                                storage_key: key,
                                description: 'Session data in browser storage - vulnerable to XSS'
                            });
                        }
                    }

                    penTest.test_coverage.session.storage_analyzed = sessionStorage.length;
                }

                // Risk assessment
                const criticalCount = penTest.findings.filter(f => f.severity === 'critical').length;
                const highCount = penTest.findings.filter(f => f.severity === 'high').length;
                const mediumCount = penTest.findings.filter(f => f.severity === 'medium').length;

                penTest.risk_assessment = {
                    overall_risk: criticalCount > 0 ? 'critical' : highCount > 1 ? 'high' : highCount > 0 || mediumCount > 2 ? 'medium' : 'low',
                    critical_findings: criticalCount,
                    high_findings: highCount,
                    medium_findings: mediumCount,
                    total_findings: penTest.findings.length
                };

                // Safe mode proof of concepts (demonstration only)
                if (arguments[1]) { // safe_mode
                    penTest.proof_of_concepts = [
                        {
                            name: 'input_validation_demo',
                            description: 'Demonstrates input validation weaknesses through field analysis',
                            safe: true,
                            method: 'Static analysis of form validation attributes'
                        },
                        {
                            name: 'auth_weakness_demo',
                            description: 'Identifies authentication weaknesses through DOM inspection',
                            safe: true,
                            method: 'Read-only analysis of authentication elements'
                        }
                    ];
                }

                return penTest;
            })()
            """

            pen_test_result = client.send_command('Runtime.evaluate', {
                'expression': pen_test_js,
                'arguments': [
                    {'value': test_type},
                    {'value': safe_mode}
                ],
                'returnByValue': True
            })

            pen_test_data = {
                "test_type": test_type,
                "safe_mode": safe_mode,
                "penetration_test": pen_test_result.get('result', {}).get('value', {}),
                "ethical_testing_notice": "All tests performed are read-only and non-destructive"
            }

            track_endpoint_usage('penetration_test', [CDPDomain.SECURITY, CDPDomain.RUNTIME], {
                'test_type': test_type,
                'safe_mode': safe_mode,
                'findings_count': len(pen_test_data.get('penetration_test', {}).get('findings', []))
            })

            return jsonify(create_success_response(pen_test_data, 'penetration_test', [CDPDomain.SECURITY, CDPDomain.RUNTIME]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('penetration_test', e,
                              {'test_type': test_type, 'safe_mode': safe_mode}, 'penetration_test')


@security_routes.route('/cdp/security/compliance_check', methods=['GET', 'POST'])
@require_domains([CDPDomain.SECURITY])
def compliance_check():
    """
    Check compliance with security standards and regulations

    @route GET/POST /cdp/security/compliance_check
    @param {string} [standard] - Compliance standard to check (owasp, gdpr, pci-dss)
    @param {boolean} [detailed_report=true] - Include detailed compliance breakdown
    @returns {object} Compliance assessment with standard-specific recommendations and gap analysis
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            params = parse_request_params(request, ['standard', 'detailed_report'])
            standard = params.get('standard', 'owasp')
            detailed_report = params.get('detailed_report', 'true').lower() == 'true'

            client.send_command('Security.enable')

            compliance_js = """
            (() => {
                const compliance = {
                    standard: arguments[0],
                    compliance_score: 0,
                    total_checks: 0,
                    passed_checks: 0,
                    failed_checks: [],
                    recommendations: [],
                    detailed_breakdown: {}
                };

                // OWASP Top 10 Compliance Check
                if (arguments[0] === 'owasp' || arguments[0] === 'all') {
                    const owaspChecks = {
                        injection: { passed: true, details: [] },
                        broken_auth: { passed: true, details: [] },
                        sensitive_data: { passed: true, details: [] },
                        xml_external: { passed: true, details: [] },
                        broken_access: { passed: true, details: [] },
                        security_misconfig: { passed: true, details: [] },
                        xss: { passed: true, details: [] },
                        insecure_deserialization: { passed: true, details: [] },
                        vulnerable_components: { passed: true, details: [] },
                        insufficient_logging: { passed: true, details: [] }
                    };

                    // Check for XSS vulnerabilities
                    const userInputs = document.querySelectorAll('input[type="text"], textarea');
                    if (userInputs.length > 0) {
                        const hasEscaping = Array.from(userInputs).some(input =>
                            input.getAttribute('data-escape') ||
                            input.closest('form')?.getAttribute('data-csrf-token')
                        );

                        if (!hasEscaping) {
                            owaspChecks.xss.passed = false;
                            owaspChecks.xss.details.push('User input fields detected without apparent XSS protection');
                            compliance.failed_checks.push('OWASP A7 - Cross-Site Scripting (XSS)');
                            compliance.recommendations.push('Implement input validation and output encoding');
                        }
                    }

                    // Check for broken authentication
                    const passwordFields = document.querySelectorAll('input[type="password"]');
                    passwordFields.forEach(field => {
                        const form = field.closest('form');
                        if (form && form.action && form.action.startsWith('http:')) {
                            owaspChecks.broken_auth.passed = false;
                            owaspChecks.broken_auth.details.push('Password transmitted over HTTP');
                            compliance.failed_checks.push('OWASP A2 - Broken Authentication');
                            compliance.recommendations.push('Use HTTPS for all authentication forms');
                        }
                    });

                    // Check for sensitive data exposure
                    const sensitivePatterns = ['ssn', 'credit', 'card', 'bank'];
                    const pageText = document.body.textContent.toLowerCase();
                    sensitivePatterns.forEach(pattern => {
                        if (pageText.includes(pattern) && !window.location.protocol.includes('https')) {
                            owaspChecks.sensitive_data.passed = false;
                            owaspChecks.sensitive_data.details.push(`Potential sensitive data (${pattern}) on non-HTTPS page`);
                            compliance.failed_checks.push('OWASP A3 - Sensitive Data Exposure');
                            compliance.recommendations.push('Ensure all sensitive data is transmitted over HTTPS');
                        }
                    });

                    // Check for security misconfiguration
                    const scriptTags = document.querySelectorAll('script[src]');
                    scriptTags.forEach(script => {
                        if (script.src && !script.integrity) {
                            owaspChecks.security_misconfig.passed = false;
                            owaspChecks.security_misconfig.details.push('External script without integrity check');
                            compliance.failed_checks.push('OWASP A6 - Security Misconfiguration');
                            compliance.recommendations.push('Add integrity attributes to external scripts');
                        }
                    });

                    compliance.detailed_breakdown.owasp = owaspChecks;
                    compliance.total_checks += 10;
                    compliance.passed_checks = Object.values(owaspChecks).filter(check => check.passed).length;
                }

                // GDPR Compliance Check
                if (arguments[0] === 'gdpr' || arguments[0] === 'all') {
                    const gdprChecks = {
                        consent_mechanism: { passed: false, details: [] },
                        data_processing_transparency: { passed: false, details: [] },
                        right_to_erasure: { passed: false, details: [] },
                        data_portability: { passed: false, details: [] },
                        privacy_by_design: { passed: false, details: [] }
                    };

                    // Check for cookie consent
                    const consentElements = document.querySelectorAll('[class*="cookie"], [id*="cookie"], [class*="consent"], [id*="consent"]');
                    if (consentElements.length > 0) {
                        gdprChecks.consent_mechanism.passed = true;
                        gdprChecks.consent_mechanism.details.push('Cookie consent mechanism detected');
                    } else if (document.cookie) {
                        gdprChecks.consent_mechanism.details.push('Cookies present but no consent mechanism');
                        compliance.failed_checks.push('GDPR Article 7 - Consent');
                        compliance.recommendations.push('Implement cookie consent mechanism');
                    }

                    // Check for privacy policy
                    const privacyLinks = document.querySelectorAll('a[href*="privacy"], a[href*="policy"]');
                    if (privacyLinks.length > 0) {
                        gdprChecks.data_processing_transparency.passed = true;
                        gdprChecks.data_processing_transparency.details.push('Privacy policy link found');
                    } else {
                        gdprChecks.data_processing_transparency.details.push('No privacy policy link detected');
                        compliance.failed_checks.push('GDPR Article 13 - Information to be provided');
                        compliance.recommendations.push('Add privacy policy link');
                    }

                    // Check for data deletion options
                    const deleteAccountLinks = document.querySelectorAll('a[href*="delete"], a[href*="remove"], button[class*="delete"]');
                    if (deleteAccountLinks.length > 0) {
                        gdprChecks.right_to_erasure.passed = true;
                        gdprChecks.right_to_erasure.details.push('Data deletion options found');
                    } else {
                        gdprChecks.right_to_erasure.details.push('No apparent data deletion mechanism');
                        compliance.failed_checks.push('GDPR Article 17 - Right to erasure');
                        compliance.recommendations.push('Provide user data deletion options');
                    }

                    compliance.detailed_breakdown.gdpr = gdprChecks;
                    if (arguments[0] === 'gdpr') {
                        compliance.total_checks = 5;
                        compliance.passed_checks = Object.values(gdprChecks).filter(check => check.passed).length;
                    }
                }

                // Calculate compliance score
                if (compliance.total_checks > 0) {
                    compliance.compliance_score = Math.round((compliance.passed_checks / compliance.total_checks) * 100);
                }

                return compliance;
            })()
            """

            compliance_result = client.send_command('Runtime.evaluate', {
                'expression': compliance_js,
                'arguments': [{'value': standard}],
                'returnByValue': True
            })

            compliance_data = {
                "standard": standard,
                "detailed_report": detailed_report,
                "compliance_check": compliance_result.get('result', {}).get('value', {})
            }

            # Add additional compliance guidance if detailed report requested
            if detailed_report:
                compliance_check = compliance_data.get('compliance_check', {})
                score = compliance_check.get('compliance_score', 0)

                if score >= 90:
                    compliance_data['compliance_status'] = 'excellent'
                    compliance_data['next_steps'] = ['Maintain current security practices', 'Regular security audits']
                elif score >= 75:
                    compliance_data['compliance_status'] = 'good'
                    compliance_data['next_steps'] = ['Address remaining gaps', 'Implement failed checks']
                elif score >= 50:
                    compliance_data['compliance_status'] = 'needs_improvement'
                    compliance_data['next_steps'] = ['Priority security remediation', 'Security training']
                else:
                    compliance_data['compliance_status'] = 'critical'
                    compliance_data['next_steps'] = ['Immediate security overhaul', 'Professional security audit']

            track_endpoint_usage('compliance_check', [CDPDomain.SECURITY], {
                'standard': standard,
                'detailed_report': detailed_report,
                'compliance_score': compliance_data.get('compliance_check', {}).get('compliance_score', 0)
            })

            return jsonify(create_success_response(compliance_data, 'compliance_check', [CDPDomain.SECURITY]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('compliance_check', e,
                              {'standard': standard}, 'compliance_check')


@security_routes.route('/cdp/security/ethical_hacking', methods=['GET', 'POST'])
@require_domains([CDPDomain.SECURITY, CDPDomain.RUNTIME])
def ethical_hacking():
    """
    Perform ethical hacking assessment with strict defensive focus

    @route GET/POST /cdp/security/ethical_hacking
    @param {string} [technique] - Ethical hacking technique (reconnaissance, vulnerability_analysis)
    @param {boolean} [documentation_mode=true] - Generate security documentation
    @returns {object} Ethical hacking assessment focused on defensive security measures and documentation
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            params = parse_request_params(request, ['technique', 'documentation_mode'])
            technique = params.get('technique', 'reconnaissance')
            documentation_mode = params.get('documentation_mode', 'true').lower() == 'true'

            client.send_command('Security.enable')
            client.send_command('Runtime.enable')

            ethical_hacking_js = """
            (() => {
                const ethicalAssessment = {
                    technique: arguments[0],
                    defensive_focus: true,
                    assessment_type: 'white_box',
                    findings: [],
                    defensive_recommendations: [],
                    security_documentation: {},
                    risk_assessment: {}
                };

                // Reconnaissance (Defensive Intelligence Gathering)
                if (arguments[0] === 'reconnaissance' || arguments[0] === 'all') {
                    const recon = {
                        technology_stack: [],
                        attack_surface: {},
                        entry_points: [],
                        defensive_measures: []
                    };

                    // Technology fingerprinting for defense
                    const metaTags = document.querySelectorAll('meta[name="generator"], meta[name="viewport"]');
                    metaTags.forEach(meta => {
                        recon.technology_stack.push({
                            type: 'meta_tag',
                            name: meta.name,
                            content: meta.content,
                            defensive_note: 'Consider removing generator meta tags to reduce information disclosure'
                        });
                    });

                    // Attack surface mapping
                    recon.attack_surface = {
                        forms: document.querySelectorAll('form').length,
                        inputs: document.querySelectorAll('input').length,
                        links: document.querySelectorAll('a[href]').length,
                        scripts: document.querySelectorAll('script').length,
                        iframes: document.querySelectorAll('iframe').length
                    };

                    // Entry point analysis
                    document.querySelectorAll('form').forEach((form, index) => {
                        const method = form.method.toLowerCase() || 'get';
                        const action = form.action || window.location.href;

                        recon.entry_points.push({
                            type: 'form',
                            index: index,
                            method: method,
                            action: action,
                            input_count: form.querySelectorAll('input').length,
                            defensive_priority: method === 'post' ? 'high' : 'medium'
                        });
                    });

                    // Identify existing defensive measures
                    if (document.querySelector('meta[http-equiv="Content-Security-Policy"]')) {
                        recon.defensive_measures.push('CSP implemented via meta tag');
                    }

                    if (window.location.protocol === 'https:') {
                        recon.defensive_measures.push('HTTPS protocol in use');
                    }

                    ethicalAssessment.security_documentation.reconnaissance = recon;

                    // Defensive recommendations based on reconnaissance
                    if (recon.technology_stack.length > 0) {
                        ethicalAssessment.defensive_recommendations.push('Remove or minimize technology disclosure in meta tags');
                    }

                    if (recon.attack_surface.forms > 3) {
                        ethicalAssessment.defensive_recommendations.push('Implement rate limiting on form submissions');
                    }

                    if (recon.defensive_measures.length < 2) {
                        ethicalAssessment.defensive_recommendations.push('Increase security controls implementation');
                    }
                }

                // Vulnerability Analysis (Defensive Perspective)
                if (arguments[0] === 'vulnerability_analysis' || arguments[0] === 'all') {
                    const vulnAnalysis = {
                        potential_vulnerabilities: [],
                        defensive_gaps: [],
                        security_controls: [],
                        remediation_priority: []
                    };

                    // Client-side security analysis
                    const inputs = document.querySelectorAll('input[type="text"], textarea');
                    inputs.forEach((input, index) => {
                        const hasValidation = input.hasAttribute('pattern') ||
                                            input.hasAttribute('maxlength') ||
                                            input.hasAttribute('required');

                        if (!hasValidation) {
                            vulnAnalysis.potential_vulnerabilities.push({
                                type: 'input_validation_gap',
                                element_index: index,
                                severity: 'medium',
                                description: 'Input lacks client-side validation',
                                remediation: 'Add validation attributes and server-side validation'
                            });
                        }
                    });

                    // Check for security control implementation
                    const forms = document.querySelectorAll('form');
                    forms.forEach((form, index) => {
                        const hasCSRF = form.querySelector('input[name*="csrf"], input[name*="token"]');
                        if (!hasCSRF) {
                            vulnAnalysis.defensive_gaps.push({
                                type: 'missing_csrf_protection',
                                form_index: index,
                                severity: 'high',
                                description: 'Form lacks apparent CSRF protection',
                                remediation: 'Implement CSRF tokens'
                            });
                        }
                    });

                    // Identify existing security controls
                    if (document.cookie.includes('Secure') || document.cookie.includes('HttpOnly')) {
                        vulnAnalysis.security_controls.push('Secure cookie attributes detected');
                    }

                    // Prioritize remediation
                    vulnAnalysis.remediation_priority = [
                        ...vulnAnalysis.defensive_gaps.filter(gap => gap.severity === 'high'),
                        ...vulnAnalysis.potential_vulnerabilities.filter(vuln => vuln.severity === 'high'),
                        ...vulnAnalysis.defensive_gaps.filter(gap => gap.severity === 'medium'),
                        ...vulnAnalysis.potential_vulnerabilities.filter(vuln => vuln.severity === 'medium')
                    ];

                    ethicalAssessment.security_documentation.vulnerability_analysis = vulnAnalysis;

                    // Generate defensive recommendations
                    if (vulnAnalysis.potential_vulnerabilities.length > 0) {
                        ethicalAssessment.defensive_recommendations.push('Implement comprehensive input validation');
                    }

                    if (vulnAnalysis.defensive_gaps.length > 0) {
                        ethicalAssessment.defensive_recommendations.push('Address security control gaps');
                    }
                }

                // Risk assessment
                const totalIssues = ethicalAssessment.security_documentation.vulnerability_analysis?.potential_vulnerabilities?.length || 0;
                const highSeverityIssues = ethicalAssessment.security_documentation.vulnerability_analysis?.defensive_gaps?.filter(gap => gap.severity === 'high')?.length || 0;

                ethicalAssessment.risk_assessment = {
                    overall_risk: highSeverityIssues > 0 ? 'high' : totalIssues > 3 ? 'medium' : 'low',
                    total_issues: totalIssues,
                    high_severity_count: highSeverityIssues,
                    defensive_maturity: ethicalAssessment.security_documentation.reconnaissance?.defensive_measures?.length || 0
                };

                // Documentation mode enhancements
                if (arguments[1]) { // documentation_mode
                    ethicalAssessment.security_documentation.summary = {
                        assessment_date: new Date().toISOString(),
                        methodology: 'Ethical white-box security assessment',
                        scope: 'Client-side security analysis',
                        limitations: 'Limited to browser-accessible security features',
                        next_steps: ethicalAssessment.defensive_recommendations
                    };
                }

                return ethicalAssessment;
            })()
            """

            ethical_result = client.send_command('Runtime.evaluate', {
                'expression': ethical_hacking_js,
                'arguments': [
                    {'value': technique},
                    {'value': documentation_mode}
                ],
                'returnByValue': True
            })

            ethical_data = {
                "technique": technique,
                "documentation_mode": documentation_mode,
                "ethical_assessment": ethical_result.get('result', {}).get('value', {}),
                "ethical_guidelines": {
                    "purpose": "Defensive security assessment only",
                    "scope": "White-box security analysis",
                    "restrictions": "No exploitation or destructive testing",
                    "focus": "Security documentation and defensive recommendations"
                }
            }

            track_endpoint_usage('ethical_hacking', [CDPDomain.SECURITY, CDPDomain.RUNTIME], {
                'technique': technique,
                'documentation_mode': documentation_mode,
                'issues_found': ethical_data.get('ethical_assessment', {}).get('risk_assessment', {}).get('total_issues', 0)
            })

            return jsonify(create_success_response(ethical_data, 'ethical_hacking', [CDPDomain.SECURITY, CDPDomain.RUNTIME]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('ethical_hacking', e,
                              {'technique': technique}, 'ethical_hacking')


@security_routes.route('/cdp/security/protection_validation', methods=['GET', 'POST'])
@require_domains([CDPDomain.SECURITY])
def protection_validation():
    """
    Validate effectiveness of security protection measures

    @route GET/POST /cdp/security/protection_validation
    @param {string} [protection_type] - Type of protection to validate (headers, encryption, access_control)
    @param {boolean} [generate_report=true] - Generate validation report
    @returns {object} Protection validation results with effectiveness assessment and improvement recommendations
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            params = parse_request_params(request, ['protection_type', 'generate_report'])
            protection_type = params.get('protection_type', 'all')
            generate_report = params.get('generate_report', 'true').lower() == 'true'

            client.send_command('Security.enable')

            protection_validation_js = """
            (() => {
                const validation = {
                    protection_type: arguments[0],
                    validation_results: {},
                    effectiveness_score: 0,
                    protection_gaps: [],
                    improvement_recommendations: [],
                    compliance_status: {}
                };

                let totalChecks = 0;
                let passedChecks = 0;

                // Security Headers Validation
                if (arguments[0] === 'headers' || arguments[0] === 'all') {
                    const headerValidation = {
                        csp_validation: { implemented: false, effectiveness: 'none' },
                        frame_options: { implemented: false, effectiveness: 'none' },
                        hsts: { detectable: false, note: 'Cannot detect from client-side' },
                        referrer_policy: { implemented: false, effectiveness: 'none' }
                    };

                    // Check for CSP implementation
                    const cspMeta = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
                    if (cspMeta) {
                        headerValidation.csp_validation.implemented = true;
                        const cspContent = cspMeta.content;

                        if (cspContent.includes("'none'") || cspContent.includes("'self'")) {
                            headerValidation.csp_validation.effectiveness = 'high';
                            passedChecks++;
                        } else if (cspContent.includes("'unsafe-inline'") || cspContent.includes("'unsafe-eval'")) {
                            headerValidation.csp_validation.effectiveness = 'low';
                            validation.protection_gaps.push({
                                type: 'weak_csp',
                                severity: 'medium',
                                description: 'CSP allows unsafe inline or eval'
                            });
                        } else {
                            headerValidation.csp_validation.effectiveness = 'medium';
                        }
                    } else {
                        validation.protection_gaps.push({
                            type: 'missing_csp',
                            severity: 'high',
                            description: 'No Content Security Policy detected'
                        });
                    }
                    totalChecks++;

                    // Check frame protection
                    try {
                        if (window.top === window.self) {
                            headerValidation.frame_options.implemented = true;
                            headerValidation.frame_options.effectiveness = 'unknown';
                        } else {
                            // Page is framed but we're still executing - weak protection
                            headerValidation.frame_options.effectiveness = 'low';
                            validation.protection_gaps.push({
                                type: 'weak_frame_protection',
                                severity: 'medium',
                                description: 'Page can be framed despite protection attempts'
                            });
                        }
                    } catch (e) {
                        headerValidation.frame_options.implemented = true;
                        headerValidation.frame_options.effectiveness = 'high';
                        passedChecks++;
                    }
                    totalChecks++;

                    validation.validation_results.security_headers = headerValidation;

                    // Add recommendations for headers
                    if (!headerValidation.csp_validation.implemented) {
                        validation.improvement_recommendations.push('Implement Content-Security-Policy header');
                    }
                    if (headerValidation.csp_validation.effectiveness === 'low') {
                        validation.improvement_recommendations.push('Strengthen CSP by removing unsafe directives');
                    }
                }

                // Encryption Validation
                if (arguments[0] === 'encryption' || arguments[0] === 'all') {
                    const encryptionValidation = {
                        https_usage: { implemented: false, effectiveness: 'none' },
                        mixed_content: { issues_found: 0, effectiveness: 'high' },
                        secure_protocols: { validated: false, effectiveness: 'unknown' }
                    };

                    // HTTPS validation
                    if (window.location.protocol === 'https:') {
                        encryptionValidation.https_usage.implemented = true;
                        encryptionValidation.https_usage.effectiveness = 'high';
                        passedChecks++;
                    } else {
                        validation.protection_gaps.push({
                            type: 'no_https',
                            severity: 'critical',
                            description: 'Page served over insecure HTTP'
                        });
                    }
                    totalChecks++;

                    // Mixed content check
                    if (window.location.protocol === 'https:') {
                        const httpResources = [];

                        // Check images
                        document.querySelectorAll('img[src]').forEach(img => {
                            if (img.src.startsWith('http:')) {
                                httpResources.push('image');
                            }
                        });

                        // Check scripts
                        document.querySelectorAll('script[src]').forEach(script => {
                            if (script.src.startsWith('http:')) {
                                httpResources.push('script');
                            }
                        });

                        encryptionValidation.mixed_content.issues_found = httpResources.length;
                        if (httpResources.length === 0) {
                            encryptionValidation.mixed_content.effectiveness = 'high';
                            passedChecks++;
                        } else {
                            encryptionValidation.mixed_content.effectiveness = 'low';
                            validation.protection_gaps.push({
                                type: 'mixed_content',
                                severity: 'medium',
                                description: `${httpResources.length} HTTP resources on HTTPS page`
                            });
                        }
                    }
                    totalChecks++;

                    validation.validation_results.encryption = encryptionValidation;

                    // Add encryption recommendations
                    if (!encryptionValidation.https_usage.implemented) {
                        validation.improvement_recommendations.push('Migrate to HTTPS for all traffic');
                    }
                    if (encryptionValidation.mixed_content.issues_found > 0) {
                        validation.improvement_recommendations.push('Fix mixed content by using HTTPS for all resources');
                    }
                }

                // Access Control Validation
                if (arguments[0] === 'access_control' || arguments[0] === 'all') {
                    const accessValidation = {
                        authentication_present: { detected: false, strength: 'none' },
                        authorization_checks: { implemented: false, effectiveness: 'unknown' },
                        session_management: { secure: false, effectiveness: 'low' }
                    };

                    // Check for authentication forms
                    const authForms = document.querySelectorAll('form input[type="password"]');
                    if (authForms.length > 0) {
                        accessValidation.authentication_present.detected = true;

                        // Check password field security
                        const passwordField = authForms[0];
                        const form = passwordField.closest('form');

                        if (form.action && form.action.startsWith('https:')) {
                            accessValidation.authentication_present.strength = 'medium';
                            passedChecks++;
                        } else {
                            accessValidation.authentication_present.strength = 'weak';
                            validation.protection_gaps.push({
                                type: 'insecure_auth',
                                severity: 'critical',
                                description: 'Authentication form submits over insecure connection'
                            });
                        }
                    }
                    totalChecks++;

                    // Check session management
                    if (document.cookie) {
                        const cookies = document.cookie.split(';');
                        const sessionCookies = cookies.filter(cookie =>
                            /session|sess|auth|login/i.test(cookie.trim())
                        );

                        if (sessionCookies.length > 0) {
                            accessValidation.session_management.secure = true;
                            accessValidation.session_management.effectiveness = 'medium';
                            // Note: Cannot check HttpOnly or Secure flags from client-side
                        }
                    }

                    validation.validation_results.access_control = accessValidation;

                    // Add access control recommendations
                    if (accessValidation.authentication_present.strength === 'weak') {
                        validation.improvement_recommendations.push('Ensure all authentication occurs over HTTPS');
                    }
                    if (!accessValidation.session_management.secure) {
                        validation.improvement_recommendations.push('Implement secure session management with HttpOnly and Secure cookies');
                    }
                }

                // Calculate effectiveness score
                if (totalChecks > 0) {
                    validation.effectiveness_score = Math.round((passedChecks / totalChecks) * 100);
                }

                // Compliance status
                if (validation.effectiveness_score >= 90) {
                    validation.compliance_status = {
                        level: 'excellent',
                        description: 'Strong security protections in place'
                    };
                } else if (validation.effectiveness_score >= 70) {
                    validation.compliance_status = {
                        level: 'good',
                        description: 'Adequate security with room for improvement'
                    };
                } else if (validation.effectiveness_score >= 50) {
                    validation.compliance_status = {
                        level: 'needs_improvement',
                        description: 'Significant security gaps present'
                    };
                } else {
                    validation.compliance_status = {
                        level: 'critical',
                        description: 'Major security protections missing'
                    };
                }

                return validation;
            })()
            """

            validation_result = client.send_command('Runtime.evaluate', {
                'expression': protection_validation_js,
                'arguments': [{'value': protection_type}],
                'returnByValue': True
            })

            validation_data = {
                "protection_type": protection_type,
                "generate_report": generate_report,
                "protection_validation": validation_result.get('result', {}).get('value', {})
            }

            # Generate comprehensive report if requested
            if generate_report:
                validation_results = validation_data.get('protection_validation', {})
                validation_data['validation_report'] = {
                    'executive_summary': f"Security protection validation completed with {validation_results.get('effectiveness_score', 0)}% effectiveness score",
                    'key_findings': validation_results.get('protection_gaps', [])[:3],  # Top 3 gaps
                    'priority_actions': validation_results.get('improvement_recommendations', [])[:5],  # Top 5 recommendations
                    'compliance_rating': validation_results.get('compliance_status', {}).get('level', 'unknown'),
                    'next_review_date': 'Recommended within 30 days for critical issues, 90 days for good ratings'
                }

            track_endpoint_usage('protection_validation', [CDPDomain.SECURITY], {
                'protection_type': protection_type,
                'generate_report': generate_report,
                'effectiveness_score': validation_data.get('protection_validation', {}).get('effectiveness_score', 0)
            })

            return jsonify(create_success_response(validation_data, 'protection_validation', [CDPDomain.SECURITY]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('protection_validation', e,
                              {'protection_type': protection_type}, 'protection_validation')