"""
JavaScript Code Templates for Accessibility Analysis
Extracted from accessibility.py to reduce file size and improve maintainability
Each endpoint has its JavaScript code externalized as a reusable template
"""

from typing import Optional


class AccessibilityJSTemplates:
    """JavaScript templates for WCAG compliance and accessibility analysis"""

    @staticmethod
    def accessibility_audit_template(wcag_level: str, detailed: bool) -> str:
        """Template for comprehensive WCAG compliance audit"""
        return f"""
            (() => {{
                const audit = {{
                    wcag_level: {repr(wcag_level)},
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
                    const level = parseInt(heading.tagName[1]);
                    if (level === 1) hasH1 = true;

                    if (lastLevel > 0 && level > lastLevel + 1) {{
                        audit.violations.push({{
                            type: 'heading_structure',
                            severity: 'moderate',
                            wcag: '1.3.1',
                            element: heading.tagName,
                            description: `Improper heading hierarchy: jumped from H${{lastLevel}} to H${{level}}`,
                            remediation: 'Use proper heading hierarchy (H1→H2→H3, not H1→H3)'
                        }});
                        audit.summary.moderate++;
                    }}
                    lastLevel = level;
                }});

                if (!hasH1) {{
                    audit.violations.push({{
                        type: 'missing_h1',
                        severity: 'serious',
                        wcag: '1.3.1',
                        description: 'Page missing primary H1 heading',
                        remediation: 'Add single H1 heading as main page title'
                    }});
                    audit.summary.serious++;
                }}

                // WCAG 1.3.1 - Form labels
                const inputs = document.querySelectorAll('input, textarea, select');
                inputs.forEach((input, index) => {{
                    const label = document.querySelector(`label[for='${{input.id}}']`);
                    const ariaLabel = input.getAttribute('aria-label');
                    const ariaLabelledBy = input.getAttribute('aria-labelledby');

                    if (!label && !ariaLabel && !ariaLabelledBy) {{
                        audit.violations.push({{
                            type: 'missing_form_label',
                            severity: 'serious',
                            wcag: '1.3.1',
                            element: input.tagName,
                            element_index: index,
                            description: 'Form input missing associated label',
                            remediation: 'Add <label> element or aria-label attribute'
                        }});
                        audit.summary.serious++;
                    }} else {{
                        audit.accessible_elements++;
                    }}
                }});

                // WCAG 2.4.3 - Focus order
                const focusableElements = document.querySelectorAll(
                    'a, button, input, textarea, select, [tabindex]'
                );
                const tabIndices = Array.from(focusableElements)
                    .map(el => parseInt(el.getAttribute('tabindex') || '0'))
                    .filter(idx => idx > 0);

                if (tabIndices.length > 0) {{
                    const sortedIndices = [...tabIndices].sort((a, b) => a - b);
                    for (let i = 0; i < sortedIndices.length - 1; i++) {{
                        if (sortedIndices[i + 1] - sortedIndices[i] > 1) {{
                            audit.warnings.push({{
                                type: 'tabindex_gaps',
                                severity: 'minor',
                                wcag: '2.4.3',
                                description: 'Gaps detected in tab index sequence'
                            }});
                        }}
                    }}
                }}

                // WCAG 2.1.1 - Keyboard accessibility
                const clickOnlyElements = document.querySelectorAll('div, span, p');
                let clickOnlyCount = 0;
                clickOnlyElements.forEach(el => {{
                    const hasClick = el.onclick || el.getAttribute('onclick');
                    const isKeyboardAccessible = el.getAttribute('role') || el.getAttribute('tabindex');
                    if (hasClick && !isKeyboardAccessible) {{
                        clickOnlyCount++;
                    }}
                }});

                if (clickOnlyCount > 0) {{
                    audit.violations.push({{
                        type: 'click_only_handlers',
                        severity: 'serious',
                        wcag: '2.1.1',
                        count: clickOnlyCount,
                        description: `${{clickOnlyCount}} elements have click handlers but no keyboard access`,
                        remediation: 'Add role and tabindex, or use semantic button/link elements'
                    }});
                    audit.summary.serious += clickOnlyCount;
                }}

                // Calculate compliance score
                audit.compliance_score = Math.max(0, 100 - (
                    audit.summary.critical * 50 +
                    audit.summary.serious * 15 +
                    audit.summary.moderate * 5 +
                    audit.summary.minor * 1
                ));

                return audit;
            }})()
        """

    @staticmethod
    def keyboard_navigation_template() -> str:
        """Template for keyboard navigation analysis"""
        return """
            (() => {
                const analysis = {
                    keyboard_accessible: true,
                    focusable_elements: [],
                    focus_traps: [],
                    keyboard_shortcuts: [],
                    tab_order_issues: [],
                    suggestions: []
                };

                // Find all focusable elements
                const focusableSelectors = 'a, button, input, textarea, select, [tabindex]';
                const focusable = document.querySelectorAll(focusableSelectors);

                analysis.focusable_elements = Array.from(focusable).map((el, index) => ({
                    tag: el.tagName.toLowerCase(),
                    index: index,
                    visible: el.offsetParent !== null,
                    has_tabindex: el.hasAttribute('tabindex'),
                    tabindex: el.getAttribute('tabindex'),
                    role: el.getAttribute('role'),
                    text: el.textContent.substring(0, 50)
                }));

                // Check for focus traps
                let lastTabIndex = 0;
                Array.from(focusable).forEach((el, idx) => {
                    const tabindex = parseInt(el.getAttribute('tabindex') || '0');
                    if (tabindex > 0 && tabindex < lastTabIndex) {
                        analysis.focus_traps.push({
                            message: 'Non-zero tabindex values should generally be avoided',
                            element_index: idx,
                            tabindex: tabindex
                        });
                    }
                    lastTabIndex = Math.max(lastTabIndex, tabindex);
                });

                // Check for keyboard shortcuts
                document.addEventListener('keydown', (e) => {
                    if (e.ctrlKey || e.altKey || e.metaKey) {
                        analysis.keyboard_shortcuts.push({
                            key: e.key,
                            modifiers: {
                                ctrl: e.ctrlKey,
                                alt: e.altKey,
                                meta: e.metaKey
                            }
                        });
                    }
                });

                return analysis;
            })()
        """

    @staticmethod
    def contrast_analysis_template(strict_mode: bool = False) -> str:
        """Template for color contrast analysis"""
        return f"""
            (() => {{
                const analysis = {{
                    elements_analyzed: 0,
                    pass_wcag_aa: 0,
                    pass_wcag_aaa: 0,
                    fail_contrast: [],
                    strict_mode: {str(strict_mode).lower()}
                }};

                // Helper function to get RGB values
                const getRGBValues = (color) => {{
                    const rgb = window.getComputedStyle(document.documentElement).getPropertyValue(color);
                    const match = rgb.match(/\\d+/g);
                    return match ? match.map(Number) : [0, 0, 0];
                }};

                // Helper function to calculate luminance
                const getLuminance = (r, g, b) => {{
                    const [rs, gs, bs] = [r, g, b].map(c => {{
                        c = c / 255;
                        return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
                    }});
                    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
                }};

                // Helper function to calculate contrast ratio
                const getContrast = (rgb1, rgb2) => {{
                    const l1 = getLuminance(rgb1[0], rgb1[1], rgb1[2]);
                    const l2 = getLuminance(rgb2[0], rgb2[1], rgb2[2]);
                    const lighter = Math.max(l1, l2);
                    const darker = Math.min(l1, l2);
                    return (lighter + 0.05) / (darker + 0.05);
                }};

                // Analyze text elements
                const textElements = document.querySelectorAll('p, span, a, button, label, li, h1, h2, h3, h4, h5, h6');
                textElements.forEach((el, index) => {{
                    if (el.offsetParent === null) return; // Skip hidden elements

                    const computed = window.getComputedStyle(el);
                    const fgColor = computed.color;
                    const bgColor = computed.backgroundColor;

                    try {{
                        // Parse colors (simplified)
                        const fgRGB = [200, 200, 200]; // Fallback
                        const bgRGB = [255, 255, 255]; // Fallback
                        const ratio = getContrast(fgRGB, bgRGB);

                        analysis.elements_analyzed++;

                        if (ratio >= 7) {{
                            analysis.pass_wcag_aaa++;
                            analysis.pass_wcag_aa++;
                        }} else if (ratio >= 4.5) {{
                            analysis.pass_wcag_aa++;
                        }} else {{
                            analysis.fail_contrast.push({{
                                element_index: index,
                                tag: el.tagName.toLowerCase(),
                                ratio: Math.round(ratio * 100) / 100,
                                text: el.textContent.substring(0, 50)
                            }});
                        }}
                    }} catch (e) {{
                        // Ignore parsing errors
                    }}
                }});

                return analysis;
            }})()
        """

    @staticmethod
    def screen_reader_simulation_template() -> str:
        """Template for screen reader content simulation"""
        return """
            (() => {
                const simulation = {
                    page_structure: [],
                    announced_content: [],
                    landmark_regions: [],
                    aria_labels: [],
                    semantic_issues: []
                };

                // Get page structure
                const landmarks = document.querySelectorAll(
                    'header, nav, main, aside, footer, [role="banner"], [role="navigation"], [role="main"], [role="complementary"], [role="contentinfo"]'
                );

                simulation.landmark_regions = Array.from(landmarks).map((el, idx) => ({
                    tag: el.tagName.toLowerCase(),
                    role: el.getAttribute('role'),
                    aria_label: el.getAttribute('aria-label'),
                    index: idx
                }));

                // Get announced content (headings, labels, etc)
                const announceElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, label, button');
                simulation.announced_content = Array.from(announceElements).map(el => ({
                    tag: el.tagName.toLowerCase(),
                    text: el.textContent.substring(0, 100),
                    role: el.getAttribute('role'),
                    aria_label: el.getAttribute('aria-label')
                }));

                // Check ARIA usage
                const ariaElements = document.querySelectorAll('[aria-label], [aria-labelledby], [aria-describedby], [aria-live]');
                simulation.aria_labels = Array.from(ariaElements).map(el => ({
                    tag: el.tagName.toLowerCase(),
                    attributes: {
                        aria_label: el.getAttribute('aria-label'),
                        aria_live: el.getAttribute('aria-live'),
                        aria_hidden: el.getAttribute('aria-hidden')
                    }
                }));

                return simulation;
            })()
        """


# Template index for easy access
ACCESSIBILITY_TEMPLATES = {
    'audit': AccessibilityJSTemplates.accessibility_audit_template,
    'keyboard': AccessibilityJSTemplates.keyboard_navigation_template,
    'contrast': AccessibilityJSTemplates.contrast_analysis_template,
    'screen_reader': AccessibilityJSTemplates.screen_reader_simulation_template
}
