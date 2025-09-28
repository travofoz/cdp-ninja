"""
Accessibility Testing Routes
WCAG compliance testing, screen reader compatibility, and UX analysis
8 endpoints for comprehensive accessibility validation
"""

import logging
from flask import Blueprint, request, jsonify
from cdp_ninja.core.cdp_pool import get_global_pool
from cdp_ninja.core.domain_manager import CDPDomain
from .route_utils import (
    require_domains, create_success_response, handle_cdp_error,
    parse_request_params, track_endpoint_usage, ACCESSIBILITY_DOMAINS
)

logger = logging.getLogger(__name__)

accessibility_routes = Blueprint('accessibility', __name__)


@accessibility_routes.route('/cdp/accessibility/audit', methods=['GET', 'POST'])
@require_domains([CDPDomain.ACCESSIBILITY, CDPDomain.DOM])
def accessibility_audit():
    """
    Comprehensive WCAG compliance audit with detailed violations and recommendations

    @route GET/POST /cdp/accessibility/audit
    @param {string} [wcag_level=AA] - WCAG compliance level (A, AA, AAA)
    @param {boolean} [detailed=true] - Include detailed violation descriptions
    @returns {object} Complete accessibility audit with WCAG violations, compliance score, and remediation guidance
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            params = parse_request_params(request, ['wcag_level', 'detailed'])
            wcag_level = params.get('wcag_level', 'AA')
            detailed = params.get('detailed', 'true').lower() == 'true'

            # Enable required domains
            client.send_command('Accessibility.enable')
            client.send_command('DOM.enable')

            # Get full accessibility tree
            accessibility_tree = client.send_command('Accessibility.getFullAXTree')

            # Comprehensive accessibility audit JavaScript
            audit_js = f"""
            (() => {{
                const audit = {{
                    wcag_level: '{wcag_level}',
                    compliance_score: 100,
                    violations: [],
                    warnings: [],
                    passed_checks: [],
                    total_elements: 0,
                    accessible_elements: 0,
                    summary: {{
                        critical: 0,
                        serious: 0,
                        moderate: 0,
                        minor: 0
                    }}
                }};

                let violationCount = 0;

                // WCAG 1.1.1 - Non-text Content (Images without alt text)
                const images = document.querySelectorAll('img');
                audit.total_elements += images.length;
                images.forEach((img, index) => {{
                    if (!img.alt && !img.getAttribute('aria-label') && !img.getAttribute('aria-labelledby')) {{
                        audit.violations.push({{
                            type: 'missing_alt_text',
                            severity: 'serious',
                            wcag: '1.1.1',
                            element: 'img',
                            element_index: index,
                            description: 'Image missing alternative text',
                            remediation: 'Add descriptive alt attribute or aria-label',
                            selector: `img:nth-of-type(${{index + 1}})`
                        }});
                        audit.summary.serious++;
                        violationCount++;
                    }} else {{
                        audit.accessible_elements++;
                    }}
                }});

                // WCAG 1.3.1 - Info and Relationships (Heading structure)
                const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
                let lastLevel = 0;
                let hasH1 = false;

                headings.forEach((heading, index) => {{
                    const level = parseInt(heading.tagName.substring(1));
                    if (level === 1) hasH1 = true;

                    if (level > lastLevel + 1 && lastLevel !== 0) {{
                        audit.violations.push({{
                            type: 'heading_skip',
                            severity: 'moderate',
                            wcag: '1.3.1',
                            element: heading.tagName.toLowerCase(),
                            description: `Heading level skipped from h${{lastLevel}} to h${{level}}`,
                            remediation: 'Use sequential heading levels',
                            selector: `${{heading.tagName.toLowerCase()}}:nth-of-type(${{index + 1}})`
                        }});
                        audit.summary.moderate++;
                        violationCount++;
                    }}
                    lastLevel = level;
                }});

                if (!hasH1 && headings.length > 0) {{
                    audit.violations.push({{
                        type: 'missing_h1',
                        severity: 'serious',
                        wcag: '1.3.1',
                        description: 'Page missing h1 heading',
                        remediation: 'Add descriptive h1 element'
                    }});
                    audit.summary.serious++;
                    violationCount++;
                }}

                // WCAG 1.4.3 - Contrast (Minimum)
                const textElements = document.querySelectorAll('p, span, div, a, button, h1, h2, h3, h4, h5, h6, li');
                textElements.forEach((el, index) => {{
                    if (el.textContent.trim()) {{
                        const styles = window.getComputedStyle(el);
                        const color = styles.color;
                        const backgroundColor = styles.backgroundColor;

                        // Simple heuristic for low contrast (needs actual contrast calculation)
                        if (color === 'rgb(128, 128, 128)' || color.includes('gray')) {{
                            audit.warnings.push({{
                                type: 'potential_low_contrast',
                                severity: 'moderate',
                                wcag: '1.4.3',
                                element: el.tagName.toLowerCase(),
                                description: 'Potential low contrast detected',
                                remediation: 'Verify contrast ratio meets WCAG {wcag_level} standards',
                                selector: `${{el.tagName.toLowerCase()}}:nth-of-type(${{index + 1}})`
                            }});
                        }}
                    }}
                }});

                // WCAG 2.1.1 - Keyboard accessibility
                const interactiveElements = document.querySelectorAll('button, a, input, select, textarea, [tabindex]');
                audit.total_elements += interactiveElements.length;

                interactiveElements.forEach((el, index) => {{
                    const tabIndex = el.getAttribute('tabindex');
                    if (tabIndex && parseInt(tabIndex) > 0) {{
                        audit.violations.push({{
                            type: 'positive_tabindex',
                            severity: 'moderate',
                            wcag: '2.1.1',
                            element: el.tagName.toLowerCase(),
                            description: 'Positive tabindex disrupts natural tab order',
                            remediation: 'Remove positive tabindex or use 0',
                            selector: `${{el.tagName.toLowerCase()}}:nth-of-type(${{index + 1}})`
                        }});
                        audit.summary.moderate++;
                        violationCount++;
                    }} else {{
                        audit.accessible_elements++;
                    }}
                }});

                // WCAG 2.4.3 - Focus Order
                const focusableElements = document.querySelectorAll('a, button, input, select, textarea, [tabindex="0"]');
                if (focusableElements.length === 0 && interactiveElements.length > 0) {{
                    audit.violations.push({{
                        type: 'no_focusable_elements',
                        severity: 'critical',
                        wcag: '2.4.3',
                        description: 'Interactive elements not keyboard accessible',
                        remediation: 'Ensure all interactive elements are focusable'
                    }});
                    audit.summary.critical++;
                    violationCount++;
                }}

                // WCAG 3.1.1 - Language of Page
                const htmlElement = document.documentElement;
                if (!htmlElement.getAttribute('lang')) {{
                    audit.violations.push({{
                        type: 'missing_lang_attribute',
                        severity: 'serious',
                        wcag: '3.1.1',
                        element: 'html',
                        description: 'Page missing language declaration',
                        remediation: 'Add lang attribute to html element'
                    }});
                    audit.summary.serious++;
                    violationCount++;
                }}

                // WCAG 4.1.1 - Parsing (Invalid HTML)
                const forms = document.querySelectorAll('form');
                forms.forEach((form, formIndex) => {{
                    const inputs = form.querySelectorAll('input');
                    const inputIds = new Set();

                    inputs.forEach((input, inputIndex) => {{
                        if (input.id) {{
                            if (inputIds.has(input.id)) {{
                                audit.violations.push({{
                                    type: 'duplicate_id',
                                    severity: 'serious',
                                    wcag: '4.1.1',
                                    element: 'input',
                                    description: `Duplicate ID '${{input.id}}' found`,
                                    remediation: 'Ensure all IDs are unique',
                                    selector: `#${{input.id}}`
                                }});
                                audit.summary.serious++;
                                violationCount++;
                            }}
                            inputIds.add(input.id);
                        }}
                    }});
                }});

                // WCAG 3.3.2 - Labels or Instructions
                const formInputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], textarea, select');
                formInputs.forEach((input, index) => {{
                    const hasLabel = input.labels && input.labels.length > 0;
                    const hasAriaLabel = input.getAttribute('aria-label');
                    const hasAriaLabelledby = input.getAttribute('aria-labelledby');
                    const hasPlaceholder = input.getAttribute('placeholder');

                    if (!hasLabel && !hasAriaLabel && !hasAriaLabelledby) {{
                        const severity = hasPlaceholder ? 'moderate' : 'serious';
                        audit.violations.push({{
                            type: 'missing_form_label',
                            severity: severity,
                            wcag: '3.3.2',
                            element: input.tagName.toLowerCase(),
                            description: 'Form input missing accessible label',
                            remediation: 'Associate input with label element or add aria-label',
                            selector: `${{input.tagName.toLowerCase()}}:nth-of-type(${{index + 1}})`
                        }});
                        audit.summary[severity]++;
                        violationCount++;
                    }}
                }});

                // Calculate compliance score
                if (violationCount === 0) {{
                    audit.compliance_score = 100;
                }} else {{
                    const deduction = (audit.summary.critical * 25) +
                                     (audit.summary.serious * 15) +
                                     (audit.summary.moderate * 10) +
                                     (audit.summary.minor * 5);
                    audit.compliance_score = Math.max(0, 100 - deduction);
                }}

                // Add passed checks for context
                if (hasH1) {{
                    audit.passed_checks.push({{
                        type: 'heading_structure',
                        wcag: '1.3.1',
                        description: 'Page has h1 heading'
                    }});
                }}

                if (htmlElement.getAttribute('lang')) {{
                    audit.passed_checks.push({{
                        type: 'page_language',
                        wcag: '3.1.1',
                        description: 'Page language declared'
                    }});
                }}

                return audit;
            }})()
            """

            audit_result = client.send_command('Runtime.evaluate', {
                'expression': audit_js,
                'returnByValue': True
            })

            audit_data = {
                "wcag_level": wcag_level,
                "detailed_analysis": detailed,
                "accessibility_audit": audit_result.get('result', {}).get('value', {}),
                "accessibility_tree_nodes": len(accessibility_tree.get('result', {}).get('nodes', [])),
                "audit_timestamp": audit_result.get('result', {}).get('value', {}).get('audit_timestamp')
            }

            # Add detailed descriptions if requested
            if detailed:
                audit_data['wcag_guidelines'] = {
                    '1.1.1': 'All non-text content must have text alternatives',
                    '1.3.1': 'Information and relationships must be programmatically determinable',
                    '1.4.3': 'Text must have sufficient contrast against background',
                    '2.1.1': 'All functionality must be keyboard accessible',
                    '2.4.3': 'Focus order must be logical and intuitive',
                    '3.1.1': 'Language of page must be programmatically determinable',
                    '3.3.2': 'Form inputs must have labels or instructions',
                    '4.1.1': 'Content must be robust and parse correctly'
                }

            track_endpoint_usage('accessibility_audit', [CDPDomain.ACCESSIBILITY, CDPDomain.DOM], {
                'wcag_level': wcag_level,
                'violations_found': len(audit_data.get('accessibility_audit', {}).get('violations', []))
            })

            return jsonify(create_success_response(audit_data, 'accessibility_audit', [CDPDomain.ACCESSIBILITY, CDPDomain.DOM]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('accessibility_audit', e,
                              {'wcag_level': wcag_level}, 'accessibility_audit')


@accessibility_routes.route('/cdp/accessibility/keyboard', methods=['GET', 'POST'])
@require_domains([CDPDomain.ACCESSIBILITY, CDPDomain.DOM])
def keyboard_navigation():
    """
    Test keyboard navigation and focus management

    @route GET/POST /cdp/accessibility/keyboard
    @param {boolean} [tab_order=true] - Test tab order sequence
    @param {boolean} [focus_visible=true] - Check focus indicators
    @returns {object} Keyboard navigation analysis with tab order, focus traps, and accessibility issues
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            params = parse_request_params(request, ['tab_order', 'focus_visible'])
            tab_order = params.get('tab_order', 'true').lower() == 'true'
            focus_visible = params.get('focus_visible', 'true').lower() == 'true'

            client.send_command('Accessibility.enable')
            client.send_command('DOM.enable')

            keyboard_test_js = f"""
            (() => {{
                const keyboard_analysis = {{
                    tab_order_test: {str(tab_order).lower()},
                    focus_visible_test: {str(focus_visible).lower()},
                    focusable_elements: [],
                    tab_sequence: [],
                    focus_issues: [],
                    skip_links: [],
                    keyboard_traps: []
                }};

                // Find all focusable elements
                const focusableSelectors = [
                    'a[href]',
                    'button:not([disabled])',
                    'input:not([disabled]):not([type="hidden"])',
                    'select:not([disabled])',
                    'textarea:not([disabled])',
                    '[tabindex]:not([tabindex="-1"])',
                    'audio[controls]',
                    'video[controls]',
                    '[contenteditable="true"]'
                ];

                const allFocusable = document.querySelectorAll(focusableSelectors.join(', '));

                allFocusable.forEach((element, index) => {{
                    const rect = element.getBoundingClientRect();
                    const styles = window.getComputedStyle(element);
                    const tabIndex = element.getAttribute('tabindex') || '0';

                    const elementInfo = {{
                        element_index: index,
                        tag_name: element.tagName.toLowerCase(),
                        type: element.type || null,
                        tabindex: tabIndex,
                        visible: rect.width > 0 && rect.height > 0 && styles.visibility !== 'hidden',
                        aria_label: element.getAttribute('aria-label'),
                        aria_labelledby: element.getAttribute('aria-labelledby'),
                        role: element.getAttribute('role'),
                        selector: `${{element.tagName.toLowerCase()}}:nth-of-type(${{Array.from(document.querySelectorAll(element.tagName)).indexOf(element) + 1}})`
                    }};

                    keyboard_analysis.focusable_elements.push(elementInfo);

                    // Check for focus visibility issues
                    if ({str(focus_visible).lower()}) {{
                        element.addEventListener('focus', () => {{
                            const focusStyles = window.getComputedStyle(element);
                            const hasOutline = focusStyles.outline !== 'none' && focusStyles.outline !== '0px';
                            const hasBoxShadow = focusStyles.boxShadow !== 'none';
                            const hasBorder = focusStyles.borderStyle !== 'none';

                            if (!hasOutline && !hasBoxShadow && !hasBorder) {{
                                keyboard_analysis.focus_issues.push({{
                                    type: 'no_focus_indicator',
                                    element_index: index,
                                    tag_name: element.tagName.toLowerCase(),
                                    description: 'Element lacks visible focus indicator',
                                    recommendation: 'Add outline, box-shadow, or border on :focus'
                                }});
                            }}
                        }});
                    }}
                }});

                // Test tab order if requested
                if ({str(tab_order).lower()}) {{
                    const tabbableElements = Array.from(allFocusable).filter(el => {{
                        const tabIndex = parseInt(el.getAttribute('tabindex') || '0');
                        return tabIndex >= 0;
                    }}).sort((a, b) => {{
                        const aIndex = parseInt(a.getAttribute('tabindex') || '0');
                        const bIndex = parseInt(b.getAttribute('tabindex') || '0');

                        // Positive tabindex elements come first, in order
                        if (aIndex > 0 && bIndex > 0) return aIndex - bIndex;
                        if (aIndex > 0) return -1;
                        if (bIndex > 0) return 1;

                        // Zero/no tabindex elements follow document order
                        return 0;
                    }});

                    tabbableElements.forEach((element, index) => {{
                        const rect = element.getBoundingClientRect();
                        keyboard_analysis.tab_sequence.push({{
                            sequence_order: index,
                            element_tag: element.tagName.toLowerCase(),
                            element_type: element.type || null,
                            tabindex: element.getAttribute('tabindex') || '0',
                            visible: rect.width > 0 && rect.height > 0,
                            text_content: element.textContent?.trim().substring(0, 50) || '',
                            aria_label: element.getAttribute('aria-label') || '',
                            position: {{
                                x: Math.round(rect.left),
                                y: Math.round(rect.top)
                            }}
                        }});
                    }});

                    // Check for logical tab order issues
                    for (let i = 1; i < keyboard_analysis.tab_sequence.length; i++) {{
                        const current = keyboard_analysis.tab_sequence[i];
                        const previous = keyboard_analysis.tab_sequence[i - 1];

                        // Flag major position jumps that might confuse users
                        const yDiff = Math.abs(current.position.y - previous.position.y);
                        const xDiff = Math.abs(current.position.x - previous.position.x);

                        if (yDiff > 200 || (yDiff > 100 && xDiff > 300)) {{
                            keyboard_analysis.focus_issues.push({{
                                type: 'illogical_tab_order',
                                sequence_jump: `${{i - 1}} to ${{i}}`,
                                description: 'Large visual jump in tab order may confuse users',
                                recommendation: 'Consider reordering elements or using tabindex'
                            }});
                        }}
                    }}
                }}

                // Check for skip links
                const skipLinks = document.querySelectorAll('a[href^="#"]');
                skipLinks.forEach((link, index) => {{
                    const href = link.getAttribute('href');
                    const targetId = href.substring(1);
                    const target = document.getElementById(targetId);

                    keyboard_analysis.skip_links.push({{
                        link_index: index,
                        link_text: link.textContent.trim(),
                        href: href,
                        target_exists: !!target,
                        target_focusable: target ? target.getAttribute('tabindex') !== null || focusableSelectors.some(sel => target.matches(sel)) : false,
                        position_in_dom: Array.from(document.querySelectorAll('a')).indexOf(link)
                    }});
                }});

                // Simple keyboard trap detection
                const firstFocusable = keyboard_analysis.tab_sequence[0];
                const lastFocusable = keyboard_analysis.tab_sequence[keyboard_analysis.tab_sequence.length - 1];

                if (firstFocusable && lastFocusable && keyboard_analysis.tab_sequence.length > 3) {{
                    // Check if page has modal-like behavior
                    const modals = document.querySelectorAll('[role="dialog"], .modal, .popup, [aria-modal="true"]');
                    modals.forEach((modal, index) => {{
                        const modalFocusable = modal.querySelectorAll(focusableSelectors.join(', '));
                        if (modalFocusable.length > 0) {{
                            keyboard_analysis.keyboard_traps.push({{
                                modal_index: index,
                                type: 'potential_modal_trap',
                                focusable_count: modalFocusable.length,
                                has_close_button: !!modal.querySelector('[aria-label*="close"], [aria-label*="Close"], .close'),
                                recommendation: 'Ensure modal traps focus and allows escape via Esc key'
                            }});
                        }}
                    }});
                }}

                return keyboard_analysis;
            }})()
            """

            keyboard_result = client.send_command('Runtime.evaluate', {
                'expression': keyboard_test_js,
                'returnByValue': True
            })

            keyboard_data = {
                "tab_order_test": tab_order,
                "focus_visible_test": focus_visible,
                "keyboard_analysis": keyboard_result.get('result', {}).get('value', {})
            }

            track_endpoint_usage('keyboard_navigation', [CDPDomain.ACCESSIBILITY, CDPDomain.DOM], {
                'tab_order': tab_order,
                'focus_visible': focus_visible,
                'focusable_elements': len(keyboard_data.get('keyboard_analysis', {}).get('focusable_elements', []))
            })

            return jsonify(create_success_response(keyboard_data, 'keyboard_navigation', [CDPDomain.ACCESSIBILITY, CDPDomain.DOM]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('keyboard_navigation', e,
                              {'tab_order': tab_order, 'focus_visible': focus_visible}, 'keyboard_navigation')


@accessibility_routes.route('/cdp/accessibility/contrast', methods=['GET', 'POST'])
@require_domains([CDPDomain.ACCESSIBILITY, CDPDomain.DOM])
def contrast_analysis():
    """
    Analyze color contrast ratios for WCAG compliance

    @route GET/POST /cdp/accessibility/contrast
    @param {boolean} [ratio_check=true] - Calculate contrast ratios
    @param {string} [minimum=AA] - Minimum WCAG level (AA or AAA)
    @returns {object} Color contrast analysis with WCAG compliance and failing elements
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            params = parse_request_params(request, ['ratio_check', 'minimum'])
            ratio_check = params.get('ratio_check', 'true').lower() == 'true'
            minimum = params.get('minimum', 'AA')

            client.send_command('Accessibility.enable')
            client.send_command('DOM.enable')

            contrast_js = f"""
            (() => {{
                const contrast_analysis = {{
                    minimum_level: '{minimum}',
                    ratio_calculation: {str(ratio_check).lower()},
                    text_elements: [],
                    contrast_failures: [],
                    compliance_summary: {{
                        total_checked: 0,
                        passing: 0,
                        failing: 0,
                        compliance_rate: 0
                    }},
                    wcag_requirements: {{
                        'AA': {{ normal: 4.5, large: 3.0 }},
                        'AAA': {{ normal: 7.0, large: 4.5 }}
                    }}
                }};

                // Utility function to convert rgb to relative luminance
                function getLuminance(r, g, b) {{
                    const [rs, gs, bs] = [r, g, b].map(c => {{
                        c = c / 255;
                        return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
                    }});
                    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
                }}

                // Calculate contrast ratio between two colors
                function getContrastRatio(color1, color2) {{
                    const l1 = getLuminance(...color1);
                    const l2 = getLuminance(...color2);
                    const lighter = Math.max(l1, l2);
                    const darker = Math.min(l1, l2);
                    return (lighter + 0.05) / (darker + 0.05);
                }}

                // Parse rgb/rgba color strings
                function parseColor(colorStr) {{
                    if (colorStr === 'rgba(0, 0, 0, 0)' || colorStr === 'transparent') {{
                        return [255, 255, 255]; // Default to white for transparent
                    }}
                    const match = colorStr.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
                    return match ? [parseInt(match[1]), parseInt(match[2]), parseInt(match[3])] : [0, 0, 0];
                }}

                // Find background color by traversing up the DOM
                function getEffectiveBackgroundColor(element) {{
                    let current = element;
                    while (current && current !== document.body) {{
                        const bgColor = window.getComputedStyle(current).backgroundColor;
                        if (bgColor && bgColor !== 'rgba(0, 0, 0, 0)' && bgColor !== 'transparent') {{
                            return parseColor(bgColor);
                        }}
                        current = current.parentElement;
                    }}
                    return [255, 255, 255]; // Default to white
                }}

                // Check if text is considered large (18pt+ or 14pt+ bold)
                function isLargeText(element) {{
                    const styles = window.getComputedStyle(element);
                    const fontSize = parseFloat(styles.fontSize);
                    const fontWeight = styles.fontWeight;

                    // 18pt = 24px, 14pt = ~18.7px
                    return fontSize >= 24 || (fontSize >= 18.7 && (fontWeight === 'bold' || parseInt(fontWeight) >= 700));
                }}

                if ({str(ratio_check).lower()}) {{
                    // Find all text elements
                    const textElements = document.querySelectorAll('p, span, div, a, button, h1, h2, h3, h4, h5, h6, li, td, th, label, legend');

                    textElements.forEach((element, index) => {{
                        const textContent = element.textContent?.trim();
                        if (!textContent || textContent.length === 0) return;

                        const styles = window.getComputedStyle(element);
                        const color = styles.color;
                        const fontSize = parseFloat(styles.fontSize);
                        const fontWeight = styles.fontWeight;

                        const foregroundColor = parseColor(color);
                        const backgroundColor = getEffectiveBackgroundColor(element);
                        const contrastRatio = getContrastRatio(foregroundColor, backgroundColor);
                        const largeText = isLargeText(element);

                        const requirements = contrast_analysis.wcag_requirements['{minimum}'];
                        const required = largeText ? requirements.large : requirements.normal;
                        const passes = contrastRatio >= required;

                        const elementData = {{
                            element_index: index,
                            tag_name: element.tagName.toLowerCase(),
                            text_sample: textContent.substring(0, 50) + (textContent.length > 50 ? '...' : ''),
                            font_size: fontSize,
                            font_weight: fontWeight,
                            is_large_text: largeText,
                            foreground_color: `rgb(${{foregroundColor.join(', ')}})`,
                            background_color: `rgb(${{backgroundColor.join(', ')}})`,
                            contrast_ratio: Math.round(contrastRatio * 100) / 100,
                            required_ratio: required,
                            passes_wcag: passes,
                            wcag_level: '{minimum}',
                            selector: `${{element.tagName.toLowerCase()}}:nth-of-type(${{Array.from(document.querySelectorAll(element.tagName)).indexOf(element) + 1}})`
                        }};

                        contrast_analysis.text_elements.push(elementData);
                        contrast_analysis.compliance_summary.total_checked++;

                        if (passes) {{
                            contrast_analysis.compliance_summary.passing++;
                        }} else {{
                            contrast_analysis.compliance_summary.failing++;
                            contrast_analysis.contrast_failures.push({{
                                ...elementData,
                                severity: contrastRatio < (required * 0.7) ? 'critical' : 'moderate',
                                improvement_needed: Math.round((required - contrastRatio) * 100) / 100,
                                suggestion: largeText
                                    ? 'Increase contrast or reduce font size/weight'
                                    : 'Increase contrast or increase font size to 18pt+'
                            }});
                        }}
                    }});

                    // Calculate compliance rate
                    if (contrast_analysis.compliance_summary.total_checked > 0) {{
                        contrast_analysis.compliance_summary.compliance_rate =
                            Math.round((contrast_analysis.compliance_summary.passing / contrast_analysis.compliance_summary.total_checked) * 100);
                    }}
                }}

                // Color blindness simulation markers
                const colorOnlyElements = document.querySelectorAll('*[style*="color:"], .error, .success, .warning, .info');
                let colorOnlyWarnings = [];

                colorOnlyElements.forEach((element, index) => {{
                    const hasText = element.textContent?.trim();
                    const hasIcon = element.querySelector('svg, img, i[class*="icon"], span[class*="icon"]');
                    const hasPattern = element.style.textDecoration || element.style.fontWeight === 'bold';

                    if (hasText && !hasIcon && !hasPattern) {{
                        colorOnlyWarnings.push({{
                            element_index: index,
                            tag_name: element.tagName.toLowerCase(),
                            warning: 'Information conveyed by color only',
                            recommendation: 'Add icons, patterns, or text indicators',
                            class_list: Array.from(element.classList),
                            text_sample: hasText.substring(0, 30)
                        }});
                    }}
                }});

                contrast_analysis.color_only_warnings = colorOnlyWarnings;

                return contrast_analysis;
            }})()
            """

            contrast_result = client.send_command('Runtime.evaluate', {
                'expression': contrast_js,
                'returnByValue': True
            })

            contrast_data = {
                "minimum_wcag_level": minimum,
                "ratio_calculation": ratio_check,
                "contrast_analysis": contrast_result.get('result', {}).get('value', {})
            }

            track_endpoint_usage('contrast_analysis', [CDPDomain.ACCESSIBILITY, CDPDomain.DOM], {
                'minimum_level': minimum,
                'ratio_check': ratio_check,
                'failures_found': len(contrast_data.get('contrast_analysis', {}).get('contrast_failures', []))
            })

            return jsonify(create_success_response(contrast_data, 'contrast_analysis', [CDPDomain.ACCESSIBILITY, CDPDomain.DOM]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('contrast_analysis', e,
                              {'minimum': minimum}, 'contrast_analysis')


@accessibility_routes.route('/cdp/accessibility/screen_reader', methods=['GET', 'POST'])
@require_domains([CDPDomain.ACCESSIBILITY, CDPDomain.DOM])
def screen_reader_simulation():
    """
    Simulate screen reader experience and accessibility tree analysis

    @route GET/POST /cdp/accessibility/screen_reader
    @param {boolean} [simulate=true] - Simulate screen reader navigation
    @param {boolean} [verbose=true] - Include detailed accessibility tree
    @returns {object} Screen reader simulation with accessible text flow and navigation landmarks
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            params = parse_request_params(request, ['simulate', 'verbose'])
            simulate = params.get('simulate', 'true').lower() == 'true'
            verbose = params.get('verbose', 'true').lower() == 'true'

            client.send_command('Accessibility.enable')
            client.send_command('DOM.enable')

            # Get accessibility tree for detailed analysis
            accessibility_tree = client.send_command('Accessibility.getFullAXTree')

            screen_reader_js = f"""
            (() => {{
                const screen_reader = {{
                    simulate_enabled: {str(simulate).lower()},
                    verbose_mode: {str(verbose).lower()},
                    reading_sequence: [],
                    landmarks: [],
                    headings_structure: [],
                    form_analysis: [],
                    accessibility_issues: [],
                    reading_statistics: {{
                        total_elements: 0,
                        accessible_elements: 0,
                        inaccessible_elements: 0,
                        reading_time_estimate: 0
                    }}
                }};

                // Simulate screen reader reading order
                if ({str(simulate).lower()}) {{
                    const walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_ELEMENT,
                        {{
                            acceptNode: function(node) {{
                                // Skip hidden elements
                                const styles = window.getComputedStyle(node);
                                if (styles.display === 'none' || styles.visibility === 'hidden') {{
                                    return NodeFilter.FILTER_REJECT;
                                }}

                                // Include elements that would be read by screen readers
                                const tagName = node.tagName.toLowerCase();
                                const hasText = node.textContent?.trim();
                                const hasAria = node.getAttribute('aria-label') || node.getAttribute('aria-labelledby');
                                const isInteractive = ['a', 'button', 'input', 'select', 'textarea'].includes(tagName);
                                const isStructural = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'nav', 'main', 'article', 'section', 'aside', 'header', 'footer'].includes(tagName);

                                if (hasText || hasAria || isInteractive || isStructural) {{
                                    return NodeFilter.FILTER_ACCEPT;
                                }}

                                return NodeFilter.FILTER_SKIP;
                            }}
                        }}
                    );

                    let currentNode;
                    let readingOrder = 0;

                    while (currentNode = walker.nextNode()) {{
                        const tagName = currentNode.tagName.toLowerCase();
                        const textContent = currentNode.textContent?.trim() || '';
                        const ariaLabel = currentNode.getAttribute('aria-label') || '';
                        const ariaLabelledby = currentNode.getAttribute('aria-labelledby') || '';
                        const role = currentNode.getAttribute('role') || '';

                        // Calculate what screen reader would announce
                        let announcement = '';

                        // Role or element type
                        if (role) {{
                            announcement += `${{role}} `;
                        }} else if (['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(tagName)) {{
                            announcement += `heading level ${{tagName.substring(1)}} `;
                        }} else if (tagName === 'button') {{
                            announcement += 'button ';
                        }} else if (tagName === 'a') {{
                            announcement += 'link ';
                        }} else if (tagName === 'input') {{
                            const type = currentNode.getAttribute('type') || 'text';
                            announcement += `${{type}} input `;
                        }}

                        // Accessible text
                        if (ariaLabel) {{
                            announcement += ariaLabel;
                        }} else if (ariaLabelledby) {{
                            const labelElement = document.getElementById(ariaLabelledby);
                            announcement += labelElement ? labelElement.textContent?.trim() : 'unlabeled';
                        }} else if (textContent) {{
                            announcement += textContent.substring(0, 100);
                        }}

                        // State information
                        if (currentNode.disabled) announcement += ' disabled';
                        if (currentNode.checked !== undefined) {{
                            announcement += currentNode.checked ? ' checked' : ' unchecked';
                        }}
                        if (currentNode.getAttribute('aria-expanded')) {{
                            announcement += currentNode.getAttribute('aria-expanded') === 'true' ? ' expanded' : ' collapsed';
                        }}

                        if (announcement.trim()) {{
                            screen_reader.reading_sequence.push({{
                                reading_order: readingOrder++,
                                element_tag: tagName,
                                element_role: role || tagName,
                                announced_text: announcement.trim(),
                                actual_text: textContent.substring(0, 50),
                                aria_label: ariaLabel,
                                is_interactive: ['a', 'button', 'input', 'select', 'textarea'].includes(tagName),
                                is_landmark: ['nav', 'main', 'article', 'section', 'aside', 'header', 'footer'].includes(tagName) || role.includes('banner') || role.includes('navigation') || role.includes('main'),
                                reading_time_seconds: Math.ceil(announcement.length / 15) // ~15 chars per second
                            }});

                            screen_reader.reading_statistics.total_elements++;
                            screen_reader.reading_statistics.reading_time_estimate += Math.ceil(announcement.length / 15);
                        }}
                    }}
                }}

                // Analyze landmarks for navigation
                const landmarks = document.querySelectorAll('nav, main, article, section, aside, header, footer, [role="banner"], [role="navigation"], [role="main"], [role="complementary"], [role="contentinfo"]');
                landmarks.forEach((landmark, index) => {{
                    const tagName = landmark.tagName.toLowerCase();
                    const role = landmark.getAttribute('role') || tagName;
                    const ariaLabel = landmark.getAttribute('aria-label') || '';
                    const ariaLabelledby = landmark.getAttribute('aria-labelledby') || '';

                    let landmarkName = ariaLabel;
                    if (!landmarkName && ariaLabelledby) {{
                        const labelElement = document.getElementById(ariaLabelledby);
                        landmarkName = labelElement ? labelElement.textContent?.trim() : '';
                    }}
                    if (!landmarkName) {{
                        // Try to find a heading inside
                        const heading = landmark.querySelector('h1, h2, h3, h4, h5, h6');
                        landmarkName = heading ? heading.textContent?.trim() : `Unnamed ${{role}}`;
                    }}

                    screen_reader.landmarks.push({{
                        landmark_index: index,
                        element_tag: tagName,
                        role: role,
                        name: landmarkName,
                        has_label: !!ariaLabel,
                        navigation_shortcut: role === 'main' ? 'Skip to main content' : `Navigate to ${{role}}`,
                        selector: `${{tagName}}:nth-of-type(${{Array.from(document.querySelectorAll(tagName)).indexOf(landmark) + 1}})`
                    }});
                }});

                // Analyze heading structure for navigation
                const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
                let previousLevel = 0;

                headings.forEach((heading, index) => {{
                    const level = parseInt(heading.tagName.substring(1));
                    const text = heading.textContent?.trim() || '';

                    const levelJump = level - previousLevel;
                    const hasValidJump = levelJump <= 1 || previousLevel === 0;

                    screen_reader.headings_structure.push({{
                        heading_index: index,
                        level: level,
                        text: text.substring(0, 100),
                        level_jump: levelJump,
                        valid_hierarchy: hasValidJump,
                        navigation_text: `Heading level ${{level}}, ${{text}}`,
                        outline_position: Array.from(document.querySelectorAll(`h${{level}}`)).indexOf(heading) + 1
                    }});

                    if (!hasValidJump && previousLevel > 0) {{
                        screen_reader.accessibility_issues.push({{
                            type: 'heading_skip',
                            severity: 'moderate',
                            description: `Heading jumps from h${{previousLevel}} to h${{level}}`,
                            element_text: text.substring(0, 50),
                            impact: 'Screen reader users may miss content organization'
                        }});
                    }}

                    previousLevel = level;
                }});

                // Analyze forms for screen reader usability
                const forms = document.querySelectorAll('form');
                forms.forEach((form, formIndex) => {{
                    const formInputs = form.querySelectorAll('input, select, textarea');
                    const formName = form.getAttribute('name') || form.getAttribute('aria-label') || `Form ${{formIndex + 1}}`;

                    let formAnalysis = {{
                        form_index: formIndex,
                        form_name: formName,
                        total_inputs: formInputs.length,
                        labeled_inputs: 0,
                        unlabeled_inputs: 0,
                        fieldsets: form.querySelectorAll('fieldset').length,
                        submit_buttons: form.querySelectorAll('button[type="submit"], input[type="submit"]').length,
                        form_issues: []
                    }};

                    formInputs.forEach((input, inputIndex) => {{
                        const hasLabel = input.labels && input.labels.length > 0;
                        const hasAriaLabel = input.getAttribute('aria-label');
                        const hasAriaLabelledby = input.getAttribute('aria-labelledby');
                        const hasPlaceholder = input.getAttribute('placeholder');

                        if (hasLabel || hasAriaLabel || hasAriaLabelledby) {{
                            formAnalysis.labeled_inputs++;
                        }} else {{
                            formAnalysis.unlabeled_inputs++;
                            formAnalysis.form_issues.push({{
                                input_index: inputIndex,
                                input_type: input.type || input.tagName.toLowerCase(),
                                issue: 'missing_label',
                                has_placeholder: !!hasPlaceholder,
                                screen_reader_impact: 'Input purpose unclear to screen readers'
                            }});
                        }}
                    }});

                    screen_reader.form_analysis.push(formAnalysis);
                }});

                // Calculate accessibility statistics
                screen_reader.reading_statistics.accessible_elements = screen_reader.reading_sequence.length;
                screen_reader.reading_statistics.inaccessible_elements = screen_reader.reading_statistics.total_elements - screen_reader.reading_statistics.accessible_elements;

                return screen_reader;
            }})()
            """

            screen_reader_result = client.send_command('Runtime.evaluate', {
                'expression': screen_reader_js,
                'returnByValue': True
            })

            screen_reader_data = {
                "simulation_enabled": simulate,
                "verbose_analysis": verbose,
                "screen_reader_analysis": screen_reader_result.get('result', {}).get('value', {}),
                "accessibility_tree_size": len(accessibility_tree.get('result', {}).get('nodes', [])) if verbose else None
            }

            if verbose:
                screen_reader_data['raw_accessibility_tree'] = accessibility_tree.get('result', {})

            track_endpoint_usage('screen_reader_simulation', [CDPDomain.ACCESSIBILITY, CDPDomain.DOM], {
                'simulate': simulate,
                'verbose': verbose,
                'reading_elements': len(screen_reader_data.get('screen_reader_analysis', {}).get('reading_sequence', []))
            })

            return jsonify(create_success_response(screen_reader_data, 'screen_reader_simulation', [CDPDomain.ACCESSIBILITY, CDPDomain.DOM]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('screen_reader_simulation', e,
                              {'simulate': simulate, 'verbose': verbose}, 'screen_reader_simulation')


@accessibility_routes.route('/cdp/accessibility/form_analysis', methods=['POST'])
@require_domains([CDPDomain.ACCESSIBILITY, CDPDomain.DOM])
def form_accessibility_analysis():
    """
    Analyze form accessibility including labels, validation, and error handling

    @route POST /cdp/accessibility/form_analysis
    @body {string} [selector=form] - CSS selector for forms to analyze
    @body {boolean} [validation=true] - Check validation accessibility
    @body {boolean} [labels=true] - Analyze label associations
    @returns {object} Form accessibility analysis with label issues, validation patterns, and error handling
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            data = request.get_json() or {}
            selector = data.get('selector', 'form')
            validation = data.get('validation', True)
            labels = data.get('labels', True)

            client.send_command('Accessibility.enable')
            client.send_command('DOM.enable')

            form_analysis_js = f"""
            (() => {{
                const form_analysis = {{
                    selector: '{selector}',
                    validation_check: {str(validation).lower()},
                    label_check: {str(labels).lower()},
                    forms_found: [],
                    accessibility_issues: [],
                    best_practices: [],
                    error_handling: []
                }};

                const forms = document.querySelectorAll('{selector}');

                forms.forEach((form, formIndex) => {{
                    const formData = {{
                        form_index: formIndex,
                        form_id: form.id || '',
                        form_name: form.getAttribute('name') || '',
                        action: form.action || '',
                        method: form.method || 'get',
                        inputs: [],
                        fieldsets: [],
                        errors: [],
                        validation_summary: {{
                            total_inputs: 0,
                            properly_labeled: 0,
                            missing_labels: 0,
                            has_validation: 0,
                            accessible_errors: 0
                        }}
                    }};

                    // Analyze fieldsets for grouping
                    const fieldsets = form.querySelectorAll('fieldset');
                    fieldsets.forEach((fieldset, fieldsetIndex) => {{
                        const legend = fieldset.querySelector('legend');
                        formData.fieldsets.push({{
                            fieldset_index: fieldsetIndex,
                            has_legend: !!legend,
                            legend_text: legend ? legend.textContent?.trim() : '',
                            input_count: fieldset.querySelectorAll('input, select, textarea').length,
                            accessibility_note: legend ? 'Properly grouped with legend' : 'Missing legend for context'
                        }});
                    }});

                    // Analyze all form inputs
                    const inputs = form.querySelectorAll('input, select, textarea');
                    formData.validation_summary.total_inputs = inputs.length;

                    inputs.forEach((input, inputIndex) => {{
                        const inputType = input.type || input.tagName.toLowerCase();
                        const inputId = input.id || '';
                        const inputName = input.name || '';

                        // Label analysis
                        let labelInfo = {{
                            has_label: false,
                            label_method: 'none',
                            label_text: '',
                            accessibility_score: 0
                        }};

                        if ({str(labels).lower()}) {{
                            // Check for associated label element
                            if (input.labels && input.labels.length > 0) {{
                                labelInfo.has_label = true;
                                labelInfo.label_method = 'label_element';
                                labelInfo.label_text = input.labels[0].textContent?.trim() || '';
                                labelInfo.accessibility_score += 3;
                            }}
                            // Check for aria-label
                            else if (input.getAttribute('aria-label')) {{
                                labelInfo.has_label = true;
                                labelInfo.label_method = 'aria_label';
                                labelInfo.label_text = input.getAttribute('aria-label');
                                labelInfo.accessibility_score += 2;
                            }}
                            // Check for aria-labelledby
                            else if (input.getAttribute('aria-labelledby')) {{
                                const labelledbyId = input.getAttribute('aria-labelledby');
                                const labelElement = document.getElementById(labelledbyId);
                                if (labelElement) {{
                                    labelInfo.has_label = true;
                                    labelInfo.label_method = 'aria_labelledby';
                                    labelInfo.label_text = labelElement.textContent?.trim() || '';
                                    labelInfo.accessibility_score += 2;
                                }}
                            }}
                            // Check for placeholder as fallback (not ideal)
                            else if (input.getAttribute('placeholder')) {{
                                labelInfo.label_method = 'placeholder_only';
                                labelInfo.label_text = input.getAttribute('placeholder');
                                labelInfo.accessibility_score += 1;
                            }}

                            if (labelInfo.has_label) {{
                                formData.validation_summary.properly_labeled++;
                            }} else {{
                                formData.validation_summary.missing_labels++;
                                form_analysis.accessibility_issues.push({{
                                    form_index: formIndex,
                                    input_index: inputIndex,
                                    type: 'missing_label',
                                    severity: 'serious',
                                    input_type: inputType,
                                    description: `Input lacks accessible label`,
                                    recommendation: 'Add <label> element or aria-label attribute'
                                }});
                            }}
                        }}

                        // Validation analysis
                        let validationInfo = {{
                            has_validation: false,
                            validation_methods: [],
                            error_association: 'none',
                            required: input.hasAttribute('required'),
                            pattern: input.getAttribute('pattern') || '',
                            accessibility_score: 0
                        }};

                        if ({str(validation).lower()}) {{
                            // Check HTML5 validation
                            if (input.hasAttribute('required')) {{
                                validationInfo.has_validation = true;
                                validationInfo.validation_methods.push('required');
                                validationInfo.accessibility_score += 1;
                            }}
                            if (input.getAttribute('pattern')) {{
                                validationInfo.has_validation = true;
                                validationInfo.validation_methods.push('pattern');
                                validationInfo.accessibility_score += 1;
                            }}
                            if (inputType === 'email' || inputType === 'url' || inputType === 'tel') {{
                                validationInfo.has_validation = true;
                                validationInfo.validation_methods.push('input_type');
                                validationInfo.accessibility_score += 1;
                            }}
                            if (input.getAttribute('min') || input.getAttribute('max')) {{
                                validationInfo.has_validation = true;
                                validationInfo.validation_methods.push('min_max');
                                validationInfo.accessibility_score += 1;
                            }}

                            // Check for error message association
                            const ariaDescribedby = input.getAttribute('aria-describedby');
                            if (ariaDescribedby) {{
                                const errorElement = document.getElementById(ariaDescribedby);
                                if (errorElement) {{
                                    validationInfo.error_association = 'aria_describedby';
                                    validationInfo.accessibility_score += 2;

                                    formData.errors.push({{
                                        input_index: inputIndex,
                                        error_id: ariaDescribedby,
                                        error_text: errorElement.textContent?.trim() || '',
                                        properly_associated: true,
                                        visible: window.getComputedStyle(errorElement).display !== 'none'
                                    }});
                                }}
                            }}

                            if (validationInfo.has_validation) {{
                                formData.validation_summary.has_validation++;
                            }}
                        }}

                        // Additional accessibility checks
                        let accessibilityNotes = [];

                        // Check for autocomplete
                        if (input.getAttribute('autocomplete')) {{
                            accessibilityNotes.push('Has autocomplete for better UX');
                        }}

                        // Check for fieldset association
                        const fieldset = input.closest('fieldset');
                        if (fieldset) {{
                            const legend = fieldset.querySelector('legend');
                            if (legend) {{
                                accessibilityNotes.push(`Grouped under: ${{legend.textContent?.trim()}}`);
                            }}
                        }}

                        // Check for description
                        const ariaDescribedby = input.getAttribute('aria-describedby');
                        if (ariaDescribedby && !formData.errors.some(e => e.error_id === ariaDescribedby)) {{
                            const descElement = document.getElementById(ariaDescribedby);
                            if (descElement) {{
                                accessibilityNotes.push('Has descriptive text');
                            }}
                        }}

                        formData.inputs.push({{
                            input_index: inputIndex,
                            input_type: inputType,
                            input_id: inputId,
                            input_name: inputName,
                            label_info: labelInfo,
                            validation_info: validationInfo,
                            accessibility_notes: accessibilityNotes,
                            overall_accessibility_score: Math.round((labelInfo.accessibility_score + validationInfo.accessibility_score) / 2)
                        }});
                    }});

                    // Analyze error handling patterns
                    const errorElements = form.querySelectorAll('.error, .invalid, [role="alert"], [aria-live]');
                    errorElements.forEach((errorEl, errorIndex) => {{
                        const isLiveRegion = errorEl.getAttribute('aria-live') || errorEl.getAttribute('role') === 'alert';
                        const associatedInput = form.querySelector(`[aria-describedby="${{errorEl.id}}"]`);

                        form_analysis.error_handling.push({{
                            form_index: formIndex,
                            error_index: errorIndex,
                            error_id: errorEl.id || '',
                            is_live_region: isLiveRegion,
                            associated_with_input: !!associatedInput,
                            error_text: errorEl.textContent?.trim() || '',
                            visibility: window.getComputedStyle(errorEl).display !== 'none',
                            accessibility_rating: (isLiveRegion ? 2 : 0) + (associatedInput ? 2 : 0)
                        }});
                    }});

                    // Calculate accessible error count
                    formData.validation_summary.accessible_errors = formData.errors.filter(e => e.properly_associated).length;

                    form_analysis.forms_found.push(formData);
                }});

                // Generate best practices recommendations
                form_analysis.forms_found.forEach((form, index) => {{
                    const completion = form.validation_summary;

                    if (completion.properly_labeled / completion.total_inputs >= 0.9) {{
                        form_analysis.best_practices.push({{
                            form_index: index,
                            practice: 'excellent_labeling',
                            description: 'Form has excellent label coverage',
                            impact: 'Screen readers can effectively navigate form'
                        }});
                    }}

                    if (form.fieldsets.length > 0 && form.fieldsets.every(fs => fs.has_legend)) {{
                        form_analysis.best_practices.push({{
                            form_index: index,
                            practice: 'proper_grouping',
                            description: 'All fieldsets have legends',
                            impact: 'Complex forms are well-organized for assistive technology'
                        }});
                    }}

                    if (completion.accessible_errors > 0) {{
                        form_analysis.best_practices.push({{
                            form_index: index,
                            practice: 'accessible_errors',
                            description: 'Error messages properly associated with inputs',
                            impact: 'Users understand validation failures clearly'
                        }});
                    }}
                }});

                return form_analysis;
            }})()
            """

            form_result = client.send_command('Runtime.evaluate', {
                'expression': form_analysis_js,
                'returnByValue': True
            })

            form_data = {
                "selector": selector,
                "validation_analysis": validation,
                "label_analysis": labels,
                "form_accessibility": form_result.get('result', {}).get('value', {})
            }

            track_endpoint_usage('form_accessibility_analysis', [CDPDomain.ACCESSIBILITY, CDPDomain.DOM], {
                'selector': selector,
                'validation': validation,
                'labels': labels,
                'forms_analyzed': len(form_data.get('form_accessibility', {}).get('forms_found', []))
            })

            return jsonify(create_success_response(form_data, 'form_accessibility_analysis', [CDPDomain.ACCESSIBILITY, CDPDomain.DOM]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('form_accessibility_analysis', e,
                              {'selector': selector}, 'form_accessibility_analysis')


@accessibility_routes.route('/cdp/accessibility/landmarks', methods=['POST'])
@require_domains([CDPDomain.ACCESSIBILITY, CDPDomain.DOM])
def landmark_navigation_analysis():
    """
    Analyze page landmarks and semantic structure for navigation

    @route POST /cdp/accessibility/landmarks
    @body {boolean} [semantic_structure=true] - Analyze semantic HTML structure
    @body {boolean} [navigation=true] - Check navigation landmarks
    @returns {object} Landmark analysis with semantic structure, navigation flow, and accessibility improvements
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            data = request.get_json() or {}
            semantic_structure = data.get('semantic_structure', True)
            navigation = data.get('navigation', True)

            client.send_command('Accessibility.enable')
            client.send_command('DOM.enable')

            landmark_js = f"""
            (() => {{
                const landmark_analysis = {{
                    semantic_structure_check: {str(semantic_structure).lower()},
                    navigation_check: {str(navigation).lower()},
                    landmarks: [],
                    semantic_elements: [],
                    navigation_structure: [],
                    accessibility_violations: [],
                    page_structure_score: 0,
                    recommendations: []
                }};

                let structureScore = 0;
                const maxScore = 20;

                // Analyze landmarks (ARIA roles and HTML5 semantic elements)
                const landmarkSelectors = [
                    'header, [role="banner"]',
                    'nav, [role="navigation"]',
                    'main, [role="main"]',
                    'article, [role="article"]',
                    'section, [role="region"]',
                    'aside, [role="complementary"]',
                    'footer, [role="contentinfo"]',
                    '[role="search"]',
                    '[role="form"]'
                ];

                landmarkSelectors.forEach(selector => {{
                    const elements = document.querySelectorAll(selector);
                    elements.forEach((element, index) => {{
                        const tagName = element.tagName.toLowerCase();
                        const role = element.getAttribute('role') || tagName;
                        const ariaLabel = element.getAttribute('aria-label') || '';
                        const ariaLabelledby = element.getAttribute('aria-labelledby') || '';

                        let landmarkName = ariaLabel;
                        if (!landmarkName && ariaLabelledby) {{
                            const labelEl = document.getElementById(ariaLabelledby);
                            landmarkName = labelEl ? labelEl.textContent?.trim() : '';
                        }}
                        if (!landmarkName) {{
                            const heading = element.querySelector('h1, h2, h3, h4, h5, h6');
                            landmarkName = heading ? heading.textContent?.trim() : '';
                        }}

                        const landmarkData = {{
                            element_index: index,
                            element_tag: tagName,
                            semantic_role: role,
                            landmark_name: landmarkName || `Unnamed ${{role}}`,
                            has_accessible_name: !!(ariaLabel || ariaLabelledby || landmarkName),
                            nesting_level: element.parentElement ? Array.from(document.querySelectorAll('*')).indexOf(element.parentElement) : 0,
                            contains_headings: element.querySelectorAll('h1, h2, h3, h4, h5, h6').length,
                            contains_links: element.querySelectorAll('a').length,
                            selector: `${{tagName}}:nth-of-type(${{Array.from(document.querySelectorAll(tagName)).indexOf(element) + 1}})`
                        }};

                        landmark_analysis.landmarks.push(landmarkData);

                        // Score landmarks
                        if (role === 'main') structureScore += 3;
                        else if (['navigation', 'banner', 'contentinfo'].includes(role)) structureScore += 2;
                        else structureScore += 1;

                        if (landmarkData.has_accessible_name) structureScore += 1;
                    }});
                }});

                // Check for required landmarks
                const hasMain = landmark_analysis.landmarks.some(l => l.semantic_role === 'main');
                const hasNavigation = landmark_analysis.landmarks.some(l => l.semantic_role === 'navigation');
                const hasBanner = landmark_analysis.landmarks.some(l => l.semantic_role === 'banner');
                const hasContentinfo = landmark_analysis.landmarks.some(l => l.semantic_role === 'contentinfo');

                if (!hasMain) {{
                    landmark_analysis.accessibility_violations.push({{
                        type: 'missing_main_landmark',
                        severity: 'serious',
                        description: 'Page missing main landmark',
                        recommendation: 'Add <main> element or role="main" to primary content area'
                    }});
                }} else {{
                    structureScore += 2;
                }}

                if (!hasNavigation && document.querySelectorAll('a').length > 5) {{
                    landmark_analysis.accessibility_violations.push({{
                        type: 'missing_navigation_landmark',
                        severity: 'moderate',
                        description: 'Page has many links but no navigation landmark',
                        recommendation: 'Add <nav> element or role="navigation" to main navigation'
                    }});
                }}

                // Analyze semantic structure
                if ({str(semantic_structure).lower()}) {{
                    const semanticElements = [
                        'header', 'nav', 'main', 'article', 'section', 'aside', 'footer',
                        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'dl'
                    ];

                    semanticElements.forEach(tagName => {{
                        const elements = document.querySelectorAll(tagName);
                        if (elements.length > 0) {{
                            landmark_analysis.semantic_elements.push({{
                                element_type: tagName,
                                count: elements.length,
                                usage_quality: tagName.match(/h[1-6]/) ? 'structural' :
                                             ['article', 'section', 'aside'].includes(tagName) ? 'sectioning' :
                                             ['header', 'nav', 'main', 'footer'].includes(tagName) ? 'landmark' : 'content',
                                accessibility_impact: ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'nav', 'main'].includes(tagName) ? 'high' : 'medium'
                            }});
                        }}
                    }});

                    // Check heading hierarchy
                    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
                    let previousLevel = 0;
                    let hasH1 = false;

                    headings.forEach((heading, index) => {{
                        const level = parseInt(heading.tagName.substring(1));
                        if (level === 1) hasH1 = true;

                        const levelJump = level - previousLevel;
                        if (levelJump > 1 && previousLevel > 0) {{
                            landmark_analysis.accessibility_violations.push({{
                                type: 'heading_level_skip',
                                severity: 'moderate',
                                heading_index: index,
                                description: `Heading jumps from h${{previousLevel}} to h${{level}}`,
                                recommendation: 'Use sequential heading levels for proper document outline'
                            }});
                        }}

                        previousLevel = level;
                    }});

                    if (!hasH1 && headings.length > 0) {{
                        landmark_analysis.accessibility_violations.push({{
                            type: 'missing_h1',
                            severity: 'serious',
                            description: 'Page has headings but no h1',
                            recommendation: 'Add h1 element as the main page heading'
                        }});
                    }} else if (hasH1) {{
                        structureScore += 2;
                    }}
                }}

                // Analyze navigation structure
                if ({str(navigation).lower()}) {{
                    const navElements = document.querySelectorAll('nav, [role="navigation"]');

                    navElements.forEach((nav, navIndex) => {{
                        const links = nav.querySelectorAll('a');
                        const lists = nav.querySelectorAll('ul, ol');
                        const hasStructure = lists.length > 0;
                        const hasSkipLink = nav.querySelector('a[href^="#"]');

                        const navData = {{
                            nav_index: navIndex,
                            nav_type: nav.tagName.toLowerCase(),
                            link_count: links.length,
                            has_list_structure: hasStructure,
                            has_skip_link: !!hasSkipLink,
                            accessible_name: nav.getAttribute('aria-label') || nav.getAttribute('aria-labelledby') || '',
                            navigation_quality: hasStructure ? 'good' : 'basic'
                        }};

                        landmark_analysis.navigation_structure.push(navData);

                        // Check for navigation issues
                        if (links.length > 7 && !hasStructure) {{
                            landmark_analysis.accessibility_violations.push({{
                                type: 'unstructured_navigation',
                                severity: 'moderate',
                                nav_index: navIndex,
                                description: 'Navigation with many links lacks list structure',
                                recommendation: 'Use <ul> or <ol> to structure navigation links'
                            }});
                        }}

                        if (!navData.accessible_name && navElements.length > 1) {{
                            landmark_analysis.accessibility_violations.push({{
                                type: 'unlabeled_navigation',
                                severity: 'moderate',
                                nav_index: navIndex,
                                description: 'Multiple navigation areas need distinguishing labels',
                                recommendation: 'Add aria-label to identify navigation purpose'
                            }});
                        }}

                        if (hasStructure) structureScore += 1;
                        if (navData.accessible_name) structureScore += 1;
                    }});

                    // Check for skip links
                    const skipLinks = document.querySelectorAll('a[href^="#main"], a[href^="#content"], a[href*="skip"]');
                    if (skipLinks.length === 0 && navElements.length > 0) {{
                        landmark_analysis.accessibility_violations.push({{
                            type: 'missing_skip_links',
                            severity: 'moderate',
                            description: 'Page has navigation but no skip links',
                            recommendation: 'Add "Skip to main content" link at beginning of page'
                        }});
                    }} else if (skipLinks.length > 0) {{
                        structureScore += 2;
                    }}
                }}

                // Generate recommendations based on analysis
                if (landmark_analysis.landmarks.length < 3) {{
                    landmark_analysis.recommendations.push({{
                        priority: 'high',
                        category: 'structure',
                        recommendation: 'Add more semantic landmarks (header, nav, main, footer)',
                        benefit: 'Improves navigation for screen reader users'
                    }});
                }}

                if (landmark_analysis.landmarks.filter(l => l.has_accessible_name).length < landmark_analysis.landmarks.length * 0.5) {{
                    landmark_analysis.recommendations.push({{
                        priority: 'medium',
                        category: 'labeling',
                        recommendation: 'Add aria-label or aria-labelledby to landmarks',
                        benefit: 'Helps users distinguish between similar landmarks'
                    }});
                }}

                if (landmark_analysis.semantic_elements.filter(s => s.usage_quality === 'structural').length === 0) {{
                    landmark_analysis.recommendations.push({{
                        priority: 'high',
                        category: 'headings',
                        recommendation: 'Implement proper heading hierarchy (h1-h6)',
                        benefit: 'Provides document outline for navigation and understanding'
                    }});
                }}

                // Calculate final structure score
                landmark_analysis.page_structure_score = Math.min(Math.round((structureScore / maxScore) * 100), 100);

                return landmark_analysis;
            }})()
            """

            landmark_result = client.send_command('Runtime.evaluate', {
                'expression': landmark_js,
                'returnByValue': True
            })

            landmark_data = {
                "semantic_structure_analysis": semantic_structure,
                "navigation_analysis": navigation,
                "landmark_analysis": landmark_result.get('result', {}).get('value', {})
            }

            track_endpoint_usage('landmark_navigation_analysis', [CDPDomain.ACCESSIBILITY, CDPDomain.DOM], {
                'semantic_structure': semantic_structure,
                'navigation': navigation,
                'landmarks_found': len(landmark_data.get('landmark_analysis', {}).get('landmarks', []))
            })

            return jsonify(create_success_response(landmark_data, 'landmark_navigation_analysis', [CDPDomain.ACCESSIBILITY, CDPDomain.DOM]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('landmark_navigation_analysis', e,
                              {'semantic_structure': semantic_structure, 'navigation': navigation}, 'landmark_navigation_analysis')


@accessibility_routes.route('/cdp/ux/flow_analysis', methods=['GET', 'POST'])
@require_domains([CDPDomain.DOM, CDPDomain.RUNTIME])
def user_flow_analysis():
    """
    Analyze user experience flow and conversion optimization

    @route GET/POST /cdp/ux/flow_analysis
    @param {boolean} [entry_points=true] - Analyze page entry points
    @param {boolean} [conversions=true] - Check conversion elements
    @returns {object} UX flow analysis with entry points, conversion paths, and user experience optimization recommendations
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            params = parse_request_params(request, ['entry_points', 'conversions'])
            entry_points = params.get('entry_points', 'true').lower() == 'true'
            conversions = params.get('conversions', 'true').lower() == 'true'

            client.send_command('DOM.enable')
            client.send_command('Runtime.enable')

            flow_analysis_js = f"""
            (() => {{
                const flow_analysis = {{
                    entry_points_analysis: {str(entry_points).lower()},
                    conversion_analysis: {str(conversions).lower()},
                    page_entry_points: [],
                    conversion_elements: [],
                    user_journey_barriers: [],
                    ux_optimization_opportunities: [],
                    cognitive_load_assessment: {{
                        total_interactive_elements: 0,
                        primary_actions: 0,
                        secondary_actions: 0,
                        cognitive_complexity: 'low'
                    }}
                }};

                // Analyze entry points
                if ({str(entry_points).lower()}) {{
                    // Check for clear value proposition
                    const headlines = document.querySelectorAll('h1, h2, .hero-title, .headline, [class*="title"]');
                    headlines.forEach((headline, index) => {{
                        const text = headline.textContent?.trim() || '';
                        const isVisible = window.getComputedStyle(headline).display !== 'none';
                        const rect = headline.getBoundingClientRect();
                        const isAboveFold = rect.top < window.innerHeight;

                        if (text.length > 0 && isVisible) {{
                            flow_analysis.page_entry_points.push({{
                                entry_point_index: index,
                                type: 'value_proposition',
                                element: headline.tagName.toLowerCase(),
                                text: text.substring(0, 100),
                                above_fold: isAboveFold,
                                visibility_score: isAboveFold && isVisible ? 3 : isVisible ? 2 : 1,
                                clarity_score: text.length > 10 && text.length < 80 ? 3 : 2
                            }});
                        }}
                    }});

                    // Check for navigation clarity
                    const navLinks = document.querySelectorAll('nav a, header a, .navigation a');
                    if (navLinks.length > 0) {{
                        const navTexts = Array.from(navLinks).map(link => link.textContent?.trim()).filter(text => text);
                        flow_analysis.page_entry_points.push({{
                            type: 'navigation',
                            link_count: navLinks.length,
                            clear_labels: navTexts.filter(text => text.length > 2 && text.length < 20).length,
                            navigation_clarity: navTexts.length > 0 ? navTexts.filter(text => text.length > 2 && text.length < 20).length / navTexts.length : 0,
                            sample_labels: navTexts.slice(0, 5)
                        }});
                    }}

                    // Check for search functionality
                    const searchInputs = document.querySelectorAll('input[type="search"], input[placeholder*="search" i], input[aria-label*="search" i]');
                    if (searchInputs.length > 0) {{
                        flow_analysis.page_entry_points.push({{
                            type: 'search_functionality',
                            search_inputs: searchInputs.length,
                            accessibility: Array.from(searchInputs).every(input =>
                                input.getAttribute('aria-label') || input.labels?.length > 0
                            ),
                            prominent_placement: Array.from(searchInputs).some(input => {{
                                const rect = input.getBoundingClientRect();
                                return rect.top < window.innerHeight * 0.3;
                            }})
                        }});
                    }}
                }}

                // Analyze conversion elements
                if ({str(conversions).lower()}) {{
                    // Primary call-to-action buttons
                    const ctaSelectors = [
                        'button[type="submit"]',
                        '.cta, .call-to-action',
                        'button:contains("Buy"), button:contains("Purchase"), button:contains("Order")',
                        'a[class*="button"], .btn',
                        'button:contains("Sign up"), button:contains("Register"), button:contains("Subscribe")',
                        'button:contains("Download"), button:contains("Get"), button:contains("Start")'
                    ];

                    const allButtons = document.querySelectorAll('button, input[type="submit"], a[class*="btn"], a[class*="button"]');
                    allButtons.forEach((button, index) => {{
                        const text = button.textContent?.trim() || button.value || '';
                        const rect = button.getBoundingClientRect();
                        const styles = window.getComputedStyle(button);

                        // Determine if this is likely a primary CTA
                        const isPrimaryCTA = /buy|purchase|order|subscribe|sign.?up|register|download|get.?started|try.?free/i.test(text);
                        const isSecondary = /learn.?more|read.?more|view|see|browse|cancel|back/i.test(text);

                        const conversionElement = {{
                            element_index: index,
                            element_type: button.tagName.toLowerCase(),
                            cta_text: text,
                            is_primary_cta: isPrimaryCTA,
                            is_secondary: isSecondary,
                            above_fold: rect.top < window.innerHeight,
                            size_pixels: {{
                                width: Math.round(rect.width),
                                height: Math.round(rect.height)
                            }},
                            color_contrast: {{
                                background: styles.backgroundColor,
                                text: styles.color,
                                has_border: styles.border !== 'none'
                            }},
                            accessibility_score: (button.getAttribute('aria-label') ? 1 : 0) +
                                               (text.length > 2 ? 1 : 0) +
                                               (rect.width > 44 && rect.height > 44 ? 1 : 0),
                            ux_quality: {{
                                clear_action: /^(buy|download|subscribe|register|sign.?up|get|start|try)\\s/i.test(text),
                                appropriate_size: rect.width > 44 && rect.height > 44,
                                visible_prominence: rect.top < window.innerHeight &&
                                                  (styles.backgroundColor !== 'rgba(0, 0, 0, 0)' || styles.border !== 'none')
                            }}
                        }};

                        flow_analysis.conversion_elements.push(conversionElement);

                        // Count for cognitive load
                        if (isPrimaryCTA) {{
                            flow_analysis.cognitive_load_assessment.primary_actions++;
                        }} else if (isSecondary) {{
                            flow_analysis.cognitive_load_assessment.secondary_actions++;
                        }}
                        flow_analysis.cognitive_load_assessment.total_interactive_elements++;
                    }});

                    // Analyze forms as conversion barriers
                    const forms = document.querySelectorAll('form');
                    forms.forEach((form, formIndex) => {{
                        const inputs = form.querySelectorAll('input:not([type="hidden"]), select, textarea');
                        const requiredInputs = form.querySelectorAll('input[required], select[required], textarea[required]');

                        if (inputs.length > 0) {{
                            const formComplexity = inputs.length > 10 ? 'high' : inputs.length > 5 ? 'medium' : 'low';

                            flow_analysis.user_journey_barriers.push({{
                                barrier_type: 'form_complexity',
                                form_index: formIndex,
                                total_fields: inputs.length,
                                required_fields: requiredInputs.length,
                                complexity_level: formComplexity,
                                optimization_opportunity: inputs.length > 7 ? 'Consider multi-step form or remove non-essential fields' : 'Form length is reasonable',
                                has_progress_indicator: !!form.querySelector('.progress, .step, [class*="progress"]'),
                                has_validation_feedback: !!form.querySelector('.error, .invalid, [aria-invalid]')
                            }});
                        }}
                    }});

                    // Check for trust signals
                    const trustSignals = document.querySelectorAll(
                        '.testimonial, .review, .rating, .security, .guarantee, .money-back, ' +
                        '[class*="trust"], [class*="secure"], [class*="verified"], [class*="certified"]'
                    );

                    if (trustSignals.length > 0) {{
                        flow_analysis.ux_optimization_opportunities.push({{
                            opportunity_type: 'trust_signals_present',
                            count: trustSignals.length,
                            impact: 'positive',
                            description: 'Trust signals found on page',
                            recommendation: 'Ensure trust signals are prominently placed near conversion elements'
                        }});
                    }} else if (flow_analysis.conversion_elements.some(el => el.is_primary_cta)) {{
                        flow_analysis.ux_optimization_opportunities.push({{
                            opportunity_type: 'missing_trust_signals',
                            impact: 'negative',
                            description: 'No trust signals found despite having CTAs',
                            recommendation: 'Add testimonials, reviews, or security badges near conversion elements'
                        }});
                    }}
                }}

                // Cognitive load assessment
                const totalCTAs = flow_analysis.cognitive_load_assessment.primary_actions +
                                 flow_analysis.cognitive_load_assessment.secondary_actions;

                if (totalCTAs > 5) {{
                    flow_analysis.cognitive_load_assessment.cognitive_complexity = 'high';
                    flow_analysis.user_journey_barriers.push({{
                        barrier_type: 'choice_overload',
                        description: `Page has ${{totalCTAs}} call-to-action elements`,
                        impact: 'May cause decision paralysis',
                        recommendation: 'Reduce number of CTAs or establish clearer visual hierarchy'
                    }});
                }} else if (totalCTAs > 2) {{
                    flow_analysis.cognitive_load_assessment.cognitive_complexity = 'medium';
                }}

                // Check for UX optimization opportunities
                const aboveFoldCTAs = flow_analysis.conversion_elements.filter(el => el.above_fold && el.is_primary_cta);
                if (aboveFoldCTAs.length === 0 && flow_analysis.conversion_elements.some(el => el.is_primary_cta)) {{
                    flow_analysis.ux_optimization_opportunities.push({{
                        opportunity_type: 'cta_below_fold',
                        impact: 'negative',
                        description: 'Primary CTAs not visible above the fold',
                        recommendation: 'Move primary call-to-action higher on page or add duplicate CTA above fold'
                    }});
                }}

                // Check for mobile optimization indicators
                const viewportMeta = document.querySelector('meta[name="viewport"]');
                if (!viewportMeta) {{
                    flow_analysis.user_journey_barriers.push({{
                        barrier_type: 'mobile_optimization',
                        description: 'Missing viewport meta tag',
                        impact: 'Poor mobile user experience',
                        recommendation: 'Add viewport meta tag for responsive design'
                    }});
                }}

                // Check button sizes for touch targets
                const smallButtons = flow_analysis.conversion_elements.filter(el =>
                    el.size_pixels.width < 44 || el.size_pixels.height < 44
                );
                if (smallButtons.length > 0) {{
                    flow_analysis.user_journey_barriers.push({{
                        barrier_type: 'touch_target_size',
                        affected_buttons: smallButtons.length,
                        description: 'Some buttons below recommended 44x44px touch target size',
                        recommendation: 'Increase button size to at least 44x44px for better mobile usability'
                    }});
                }}

                return flow_analysis;
            }})()
            """

            flow_result = client.send_command('Runtime.evaluate', {
                'expression': flow_analysis_js,
                'returnByValue': True
            })

            flow_data = {
                "entry_points_analysis": entry_points,
                "conversion_analysis": conversions,
                "ux_flow_analysis": flow_result.get('result', {}).get('value', {})
            }

            track_endpoint_usage('user_flow_analysis', [CDPDomain.DOM, CDPDomain.RUNTIME], {
                'entry_points': entry_points,
                'conversions': conversions,
                'conversion_elements': len(flow_data.get('ux_flow_analysis', {}).get('conversion_elements', []))
            })

            return jsonify(create_success_response(flow_data, 'user_flow_analysis', [CDPDomain.DOM, CDPDomain.RUNTIME]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('user_flow_analysis', e,
                              {'entry_points': entry_points, 'conversions': conversions}, 'user_flow_analysis')


@accessibility_routes.route('/cdp/ux/responsive', methods=['GET', 'POST'])
@require_domains([CDPDomain.DOM, CDPDomain.RUNTIME])
def responsive_design_analysis():
    """
    Analyze responsive design and mobile user experience

    @route GET/POST /cdp/ux/responsive
    @param {boolean} [breakpoints=true] - Test different viewport breakpoints
    @param {boolean} [touch_friendly=true] - Check touch-friendly design
    @returns {object} Responsive design analysis with breakpoint testing, touch target analysis, and mobile UX recommendations
    """
    try:
        pool = get_global_pool()
        if not pool:
            return jsonify({"error": "CDP pool not available"}), 503

        client = pool.acquire()
        if not client:
            return jsonify({"error": "No CDP connections available"}), 503

        try:
            params = parse_request_params(request, ['breakpoints', 'touch_friendly'])
            breakpoints = params.get('breakpoints', 'true').lower() == 'true'
            touch_friendly = params.get('touch_friendly', 'true').lower() == 'true'

            client.send_command('DOM.enable')
            client.send_command('Runtime.enable')

            # Test different viewport sizes if breakpoints requested
            viewport_tests = []
            if breakpoints:
                viewports = [
                    {'width': 320, 'height': 568, 'name': 'mobile_small'},
                    {'width': 375, 'height': 667, 'name': 'mobile_medium'},
                    {'width': 768, 'height': 1024, 'name': 'tablet'},
                    {'width': 1024, 'height': 768, 'name': 'tablet_landscape'},
                    {'width': 1200, 'height': 800, 'name': 'desktop'}
                ]

                for viewport in viewports:
                    # Set viewport
                    client.send_command('Emulation.setDeviceMetricsOverride', {
                        'width': viewport['width'],
                        'height': viewport['height'],
                        'deviceScaleFactor': 1,
                        'mobile': viewport['width'] < 768
                    })

                    responsive_test_js = f"""
                    (() => {{
                        const viewport_analysis = {{
                            viewport_name: '{viewport["name"]}',
                            viewport_size: {{
                                width: {viewport['width']},
                                height: {viewport['height']}
                            }},
                            layout_issues: [],
                            overflow_elements: [],
                            touch_targets: [],
                            readability: {{
                                font_sizes: [],
                                line_heights: [],
                                text_contrast: []
                            }}
                        }};

                        // Check for horizontal overflow
                        const allElements = document.querySelectorAll('*');
                        allElements.forEach((element, index) => {{
                            if (index > 100) return; // Limit for performance

                            const rect = element.getBoundingClientRect();
                            const styles = window.getComputedStyle(element);

                            if (rect.right > window.innerWidth + 10) {{ // 10px tolerance
                                viewport_analysis.overflow_elements.push({{
                                    element_index: index,
                                    element_tag: element.tagName.toLowerCase(),
                                    overflow_amount: Math.round(rect.right - window.innerWidth),
                                    element_width: Math.round(rect.width),
                                    has_fixed_width: styles.width && styles.width.includes('px'),
                                    class_list: Array.from(element.classList).slice(0, 3)
                                }});
                            }}
                        }});

                        // Check touch targets on mobile viewports
                        if ({viewport['width']} < 768 && {str(touch_friendly).lower()}) {{
                            const interactiveElements = document.querySelectorAll('button, a, input, select, textarea, [onclick], [role="button"]');
                            interactiveElements.forEach((element, index) => {{
                                const rect = element.getBoundingClientRect();
                                const tooSmall = rect.width < 44 || rect.height < 44;
                                const text = element.textContent?.trim() || element.value || '';

                                viewport_analysis.touch_targets.push({{
                                    element_index: index,
                                    element_tag: element.tagName.toLowerCase(),
                                    size: {{
                                        width: Math.round(rect.width),
                                        height: Math.round(rect.height)
                                    }},
                                    meets_44px_minimum: !tooSmall,
                                    text_content: text.substring(0, 30),
                                    touch_friendly_score: tooSmall ? 1 : rect.width >= 48 && rect.height >= 48 ? 3 : 2
                                }});
                            }});
                        }}

                        // Check text readability
                        const textElements = document.querySelectorAll('p, span, div, a, button, h1, h2, h3, h4, h5, h6, li');
                        const fontSizeSamples = [];

                        for (let i = 0; i < Math.min(textElements.length, 20); i++) {{
                            const element = textElements[i];
                            if (element.textContent?.trim()) {{
                                const styles = window.getComputedStyle(element);
                                const fontSize = parseFloat(styles.fontSize);
                                const lineHeight = parseFloat(styles.lineHeight) || fontSize * 1.2;

                                fontSizeSamples.push({{
                                    font_size: fontSize,
                                    line_height: lineHeight,
                                    element_tag: element.tagName.toLowerCase(),
                                    readable_on_mobile: fontSize >= 16 && lineHeight >= fontSize * 1.2
                                }});
                            }}
                        }}

                        viewport_analysis.readability.font_sizes = fontSizeSamples;

                        // Check for common responsive issues
                        const images = document.querySelectorAll('img');
                        images.forEach((img, index) => {{
                            if (index > 10) return; // Limit check
                            const rect = img.getBoundingClientRect();
                            if (rect.width > window.innerWidth) {{
                                viewport_analysis.layout_issues.push({{
                                    issue_type: 'image_overflow',
                                    element_tag: 'img',
                                    description: 'Image wider than viewport',
                                    recommendation: 'Add max-width: 100% to images'
                                }});
                            }}
                        }});

                        return viewport_analysis;
                    }})()
                    """

                    viewport_result = client.send_command('Runtime.evaluate', {
                        'expression': responsive_test_js,
                        'returnByValue': True
                    })

                    viewport_tests.append(viewport_result.get('result', {}).get('value', {}))

                # Reset viewport
                client.send_command('Emulation.clearDeviceMetricsOverride')

            # Overall responsive analysis
            responsive_analysis_js = f"""
            (() => {{
                const responsive_analysis = {{
                    breakpoint_testing: {str(breakpoints).lower()},
                    touch_friendly_testing: {str(touch_friendly).lower()},
                    meta_viewport: null,
                    css_media_queries: [],
                    responsive_images: [],
                    layout_flexibility: {{
                        flexible_containers: 0,
                        fixed_width_elements: 0,
                        responsive_units: []
                    }},
                    mobile_ux_issues: [],
                    responsive_score: 0
                }};

                let score = 0;
                const maxScore = 20;

                // Check viewport meta tag
                const viewportMeta = document.querySelector('meta[name="viewport"]');
                if (viewportMeta) {{
                    responsive_analysis.meta_viewport = {{
                        content: viewportMeta.getAttribute('content'),
                        has_width_device: viewportMeta.content.includes('width=device-width'),
                        has_initial_scale: viewportMeta.content.includes('initial-scale'),
                        properly_configured: viewportMeta.content.includes('width=device-width') &&
                                           viewportMeta.content.includes('initial-scale=1')
                    }};

                    if (responsive_analysis.meta_viewport.properly_configured) {{
                        score += 3;
                    }} else if (responsive_analysis.meta_viewport.has_width_device) {{
                        score += 2;
                    }} else {{
                        score += 1;
                    }}
                }} else {{
                    responsive_analysis.mobile_ux_issues.push({{
                        issue_type: 'missing_viewport_meta',
                        severity: 'critical',
                        description: 'Missing viewport meta tag',
                        impact: 'Page will not scale properly on mobile devices',
                        recommendation: 'Add <meta name="viewport" content="width=device-width, initial-scale=1">'
                    }});
                }}

                // Check for CSS media queries (indirect check via computed styles)
                const testElement = document.createElement('div');
                testElement.style.cssText = 'width: 100%; max-width: none;';
                document.body.appendChild(testElement);

                const computedWidth = window.getComputedStyle(testElement).width;
                document.body.removeChild(testElement);

                // This is a basic check - in real implementation, we'd need server-side CSS analysis
                responsive_analysis.css_media_queries.push({{
                    detected_responsive_css: computedWidth === '100%',
                    note: 'Limited client-side detection of media queries'
                }});

                // Check responsive images
                const images = document.querySelectorAll('img');
                images.forEach((img, index) => {{
                    const hasSrcset = img.hasAttribute('srcset');
                    const hasSizes = img.hasAttribute('sizes');
                    const styles = window.getComputedStyle(img);
                    const hasResponsiveCSS = styles.maxWidth === '100%' || styles.width === '100%';

                    responsive_analysis.responsive_images.push({{
                        image_index: index,
                        has_srcset: hasSrcset,
                        has_sizes: hasSizes,
                        has_responsive_css: hasResponsiveCSS,
                        responsive_score: (hasSrcset ? 2 : 0) + (hasSizes ? 1 : 0) + (hasResponsiveCSS ? 1 : 0),
                        src: img.src.substring(0, 50) + (img.src.length > 50 ? '...' : '')
                    }});

                    if (hasSrcset || hasResponsiveCSS) score += 0.5;
                }});

                // Check layout flexibility
                const containers = document.querySelectorAll('div, section, article, main, aside, header, footer');
                containers.forEach((container, index) => {{
                    if (index > 50) return; // Limit for performance

                    const styles = window.getComputedStyle(container);
                    const hasFlexbox = styles.display === 'flex' || styles.display === 'inline-flex';
                    const hasGrid = styles.display === 'grid' || styles.display === 'inline-grid';
                    const hasPercentageWidth = styles.width && styles.width.includes('%');
                    const hasFixedWidth = styles.width && styles.width.includes('px') && !styles.maxWidth;

                    if (hasFlexbox || hasGrid || hasPercentageWidth) {{
                        responsive_analysis.layout_flexibility.flexible_containers++;
                        score += 0.2;
                    }}

                    if (hasFixedWidth) {{
                        responsive_analysis.layout_flexibility.fixed_width_elements++;
                    }}

                    // Check for responsive units
                    const responsiveUnits = ['%', 'vw', 'vh', 'em', 'rem'];
                    responsiveUnits.forEach(unit => {{
                        if (styles.width?.includes(unit) || styles.height?.includes(unit) ||
                            styles.padding?.includes(unit) || styles.margin?.includes(unit)) {{
                            if (!responsive_analysis.layout_flexibility.responsive_units.includes(unit)) {{
                                responsive_analysis.layout_flexibility.responsive_units.push(unit);
                            }}
                        }}
                    }});
                }});

                // Additional mobile UX checks
                if ({str(touch_friendly).lower()}) {{
                    // Check for horizontal scrolling elements
                    const scrollableElements = Array.from(document.querySelectorAll('*')).filter(el => {{
                        const styles = window.getComputedStyle(el);
                        return styles.overflowX === 'scroll' || styles.overflowX === 'auto';
                    }});

                    if (scrollableElements.length > 0) {{
                        responsive_analysis.mobile_ux_issues.push({{
                            issue_type: 'horizontal_scroll_elements',
                            count: scrollableElements.length,
                            description: 'Elements with horizontal scrolling detected',
                            recommendation: 'Ensure horizontal scrolling is intentional and provides good UX'
                        }});
                    }}

                    // Check text size for mobile readability
                    const smallTextElements = Array.from(document.querySelectorAll('*')).filter(el => {{
                        if (!el.textContent?.trim()) return false;
                        const fontSize = parseFloat(window.getComputedStyle(el).fontSize);
                        return fontSize < 16;
                    }});

                    if (smallTextElements.length > 5) {{
                        responsive_analysis.mobile_ux_issues.push({{
                            issue_type: 'small_text',
                            count: smallTextElements.length,
                            description: 'Many elements with text smaller than 16px',
                            recommendation: 'Increase font size to at least 16px for mobile readability'
                        }});
                    }}
                }}

                // Calculate final responsive score
                responsive_analysis.responsive_score = Math.min(Math.round((score / maxScore) * 100), 100);

                return responsive_analysis;
            }})()
            """

            responsive_result = client.send_command('Runtime.evaluate', {
                'expression': responsive_analysis_js,
                'returnByValue': True
            })

            responsive_data = {
                "breakpoint_testing": breakpoints,
                "touch_friendly_analysis": touch_friendly,
                "viewport_tests": viewport_tests if breakpoints else [],
                "responsive_analysis": responsive_result.get('result', {}).get('value', {})
            }

            track_endpoint_usage('responsive_design_analysis', [CDPDomain.DOM, CDPDomain.RUNTIME], {
                'breakpoints': breakpoints,
                'touch_friendly': touch_friendly,
                'viewport_tests_run': len(viewport_tests)
            })

            return jsonify(create_success_response(responsive_data, 'responsive_design_analysis', [CDPDomain.DOM, CDPDomain.RUNTIME]))

        finally:
            pool.release(client)

    except Exception as e:
        return handle_cdp_error('responsive_design_analysis', e,
                              {'breakpoints': breakpoints, 'touch_friendly': touch_friendly}, 'responsive_design_analysis')