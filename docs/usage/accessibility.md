# Accessibility API

*Auto-generated from accessibility.py JSDoc comments*

## GET/POST /cdp/accessibility/audit

**Function:** `accessibility_audit()`

Comprehensive WCAG compliance audit with detailed violations and recommendations

**Parameters:**
- `wcag_level=AA` *(string)* *(optional)*: WCAG compliance level (A, AA, AAA)
- `detailed=true` *(boolean)* *(optional)*: Include detailed violation descriptions

**Returns:** {object} Complete accessibility audit with WCAG violations, compliance score, and remediation guidance

---

## GET/POST /cdp/accessibility/keyboard

**Function:** `keyboard_navigation()`

Test keyboard navigation and focus management

**Parameters:**
- `tab_order=true` *(boolean)* *(optional)*: Test tab order sequence
- `focus_visible=true` *(boolean)* *(optional)*: Check focus indicators

**Returns:** {object} Keyboard navigation analysis with tab order, focus traps, and accessibility issues

---

## GET/POST /cdp/accessibility/contrast

**Function:** `contrast_analysis()`

Analyze color contrast ratios for WCAG compliance

**Parameters:**
- `ratio_check=true` *(boolean)* *(optional)*: Calculate contrast ratios
- `minimum=AA` *(string)* *(optional)*: Minimum WCAG level (AA or AAA)

**Returns:** {object} Color contrast analysis with WCAG compliance and failing elements

---

## GET/POST /cdp/accessibility/screen_reader

**Function:** `screen_reader_simulation()`

Simulate screen reader experience and accessibility tree analysis

**Parameters:**
- `simulate=true` *(boolean)* *(optional)*: Simulate screen reader navigation
- `verbose=true` *(boolean)* *(optional)*: Include detailed accessibility tree

**Returns:** {object} Screen reader simulation with accessible text flow and navigation landmarks

---

## POST /cdp/accessibility/form_analysis

**Function:** `form_accessibility_analysis()`

Analyze form accessibility including labels, validation, and error handling

**Returns:** {object} Form accessibility analysis with label issues, validation patterns, and error handling

---

## POST /cdp/accessibility/landmarks

**Function:** `landmark_navigation_analysis()`

Analyze page landmarks and semantic structure for navigation

**Returns:** {object} Landmark analysis with semantic structure, navigation flow, and accessibility improvements

---

## GET/POST /cdp/ux/flow_analysis

**Function:** `user_flow_analysis()`

Analyze user experience flow and conversion optimization

**Parameters:**
- `entry_points=true` *(boolean)* *(optional)*: Analyze page entry points
- `conversions=true` *(boolean)* *(optional)*: Check conversion elements

**Returns:** {object} UX flow analysis with entry points, conversion paths, and user experience optimization recommendations

---

## GET/POST /cdp/ux/responsive

**Function:** `responsive_design_analysis()`

Analyze responsive design and mobile user experience

**Parameters:**
- `breakpoints=true` *(boolean)* *(optional)*: Test different viewport breakpoints
- `touch_friendly=true` *(boolean)* *(optional)*: Check touch-friendly design

**Returns:** {object} Responsive design analysis with breakpoint testing, touch target analysis, and mobile UX recommendations

---

