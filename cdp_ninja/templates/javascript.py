"""
JavaScript Code Templates for CDP Operations
Eliminates duplication of JavaScript patterns across CDP commands
⚠️ NO INPUT VALIDATION - Raw string interpolation for security testing
"""

from typing import Optional, Dict, Any


class JSTemplates:
    """Reusable JavaScript templates for common CDP operations

    ⚠️ WARNING: These templates use raw string interpolation to allow
    injection testing. This is intentional for security research.
    """

    @staticmethod
    def get_element_center_coordinates(selector: str) -> str:
        """Generate JS to get element center coordinates"""
        return f"""
        (() => {{
            const selector = '{selector}';
            const el = document.querySelector(selector);
            if (el) {{
                const rect = el.getBoundingClientRect();
                return {{x: rect.x + rect.width/2, y: rect.y + rect.height/2}};
            }}
            return null;
        }})()
        """

    @staticmethod
    def check_element_exists(selector: str) -> str:
        """Generate JS to check if element exists"""
        return f"""
        (() => {{
            const selector = '{selector}';
            const el = document.querySelector(selector);
            return el !== null;
        }})()
        """

    @staticmethod
    def get_element_bounds(selector: str) -> str:
        """Generate JS to get element bounding rectangle"""
        return f"""
        (() => {{
            const selector = '{selector}';
            const el = document.querySelector(selector);
            if (el) {{
                const rect = el.getBoundingClientRect();
                return {{
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height,
                    top: rect.top,
                    left: rect.left,
                    bottom: rect.bottom,
                    right: rect.right
                }};
            }}
            return null;
        }})()
        """

    @staticmethod
    def get_element_attribute(selector: str, attribute: str) -> str:
        """Generate JS to get element attribute value"""
        return f"""
        (() => {{
            const selector = '{selector}';
            const attribute = '{attribute}';
            const el = document.querySelector(selector);
            if (el) {{
                return el.getAttribute(attribute);
            }}
            return null;
        }})()
        """

    @staticmethod
    def set_element_attribute(selector: str, attribute: str, value: str) -> str:
        """Generate JS to set element attribute value with detailed response"""
        return f"""
        (() => {{
            const selector = '{selector}';
            const attrName = '{attribute}';
            const attrValue = '{value}';
            const el = document.querySelector(selector);
            if (el) {{
                el.setAttribute(attrName, attrValue);
                return {{success: true, selector: selector, attribute: attrName, value: attrValue}};
            }}
            return {{success: false, error: 'Element not found'}};
        }})()
        """

    @staticmethod
    def get_element_html(selector: str) -> str:
        """Generate JS to get element innerHTML"""
        return f"""
        (() => {{
            const selector = '{selector}';
            const el = document.querySelector(selector);
            if (el) {{
                return el.innerHTML;
            }}
            return null;
        }})()
        """

    @staticmethod
    def set_element_html(selector: str, html: str) -> str:
        """Generate JS to set element innerHTML with detailed response"""
        return f"""
        (() => {{
            const selector = '{selector}';
            const htmlContent = '{html}';
            const el = document.querySelector(selector);
            if (el) {{
                el.innerHTML = htmlContent;
                return {{success: true, selector: selector, html_length: el.innerHTML.length}};
            }}
            return {{success: false, error: 'Element not found'}};
        }})()
        """

    @staticmethod
    def get_element_text(selector: str) -> str:
        """Generate JS to get element textContent"""
        return f"""
        (() => {{
            const selector = '{selector}';
            const el = document.querySelector(selector);
            if (el) {{
                return el.textContent;
            }}
            return null;
        }})()
        """

    @staticmethod
    def set_element_text(selector: str, text: str) -> str:
        """Generate JS to set element textContent"""
        return f"""
        (() => {{
            const selector = '{selector}';
            const text = '{text}';
            const el = document.querySelector(selector);
            if (el) {{
                el.textContent = text;
                return true;
            }}
            return false;
        }})()
        """

    @staticmethod
    def scroll_element_into_view(selector: str, behavior: str = "smooth") -> str:
        """Generate JS to scroll element into view"""
        return f"""
        (() => {{
            const selector = '{selector}';
            const behavior = '{behavior}';
            const el = document.querySelector(selector);
            if (el) {{
                el.scrollIntoView({{ behavior: behavior, block: 'center' }});
                return true;
            }}
            return false;
        }})()
        """

    @staticmethod
    def focus_element(selector: str) -> str:
        """Generate JS to focus element"""
        return f"""
        (() => {{
            const selector = '{selector}';
            const el = document.querySelector(selector);
            if (el) el.focus();
        }})()
        """

    @staticmethod
    def click_element(selector: str) -> str:
        """Generate JS to click element with detailed response"""
        return f"""
        (() => {{
            const selector = '{selector}';
            const el = document.querySelector(selector);
            if (el) {{
                el.click();
                return {{success: true, selector: selector}};
            }}
            return {{success: false, error: 'Element not found'}};
        }})()
        """

    @staticmethod
    def fill_form_field(selector: str, value: str) -> str:
        """Generate JS to fill form field - ALLOWS INJECTION for security testing"""
        return f"""
        (() => {{
            const selector = '{selector}';
            const value = '{value}';
            const el = document.querySelector(selector);
            if (el) {{
                el.value = value;
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
                return true;
            }}
            return false;
        }})()
        """

    @staticmethod
    def get_form_data(form_selector: str) -> str:
        """Generate JS to extract comprehensive form data"""
        return f"""
        (() => {{
            const selector = '{form_selector}';
            const form = document.querySelector(selector);
            if (!form) return {{error: 'Form not found'}};

            const values = {{}};
            const inputs = form.querySelectorAll('input, textarea, select');

            inputs.forEach(input => {{
                const name = input.name || input.id;
                if (name) {{
                    if (input.type === 'checkbox' || input.type === 'radio') {{
                        values[name] = input.checked;
                    }} else if (input.type === 'file') {{
                        values[name] = input.files.length > 0 ? input.files[0].name : null;
                    }} else {{
                        values[name] = input.value;
                    }}
                }}
            }});

            return {{
                selector: selector,
                values: values,
                fieldCount: inputs.length
            }};
        }})()
        """

    @staticmethod
    def evaluate_custom_js(js_code: str) -> str:
        """Execute raw JavaScript - NO SAFETY for security testing"""
        return f"""
        (() => {{
            return ({js_code});
        }})()
        """