# Browser Interaction API

*Auto-generated from browser.py JSDoc comments*

## POST /cdp/click

**Function:** `click_element()`

Click on element by selector or coordinates - RAW mode

**Parameters:**
- `selector` *(string)* *(optional)*: ANY selector, malformed or not
- `x` *(number)* *(optional)*: ANY x coordinate, can be negative/huge
- `y` *(number)* *(optional)*: ANY y coordinate, can be negative/huge
- `button` *(string)* *(optional)*: Mouse button (left/right/middle)
- `clickCount` *(number)* *(optional)*: Number of clicks

**Returns:** {object} Whatever Chrome returns (or crashes)

**Examples:**
```javascript
// Normal click
{"selector": "#submit-button"}
// Injection attempt - we WANT to test this
{"selector": "';alert('xss')//"}
// Malformed selector - see if Chrome handles it
{"selector": ">>>>invalid>>>>"}
// Extreme coordinates - test bounds
{"x": 999999999, "y": -999999999}
// Rapid multi-click
{"selector": "#button", "clickCount": 10}
```

---

## POST /cdp/type

**Function:** `type_text()`

Type text into element or focused input - RAW mode

**Parameters:**
- `text ` *(string)*: ANY text, including control characters
- `selector` *(string)* *(optional)*: Element to focus first (optional)
- `delay` *(number)* *(optional)*: Delay between characters in ms

**Returns:** {object} Success status or crash data

**Examples:**
```javascript
// Normal typing
{"text": "hello world", "selector": "#input"}
// Special characters - test edge cases
{"text": "\n\t\r\0"}
// Huge text - test limits
{"text": "A".repeat(100000)}
// Control characters
{"text": "\u0000\u0001\u0002"}
```

---

## POST /cdp/scroll

**Function:** `scroll_page()`

Scroll the page - ANY direction, ANY amount

**Parameters:**
- `direction` *(string)* *(optional)*: Direction (up/down/left/right)
- `amount` *(number)* *(optional)*: Scroll amount in pixels
- `x` *(number)* *(optional)*: X coordinate for scroll origin
- `y` *(number)* *(optional)*: Y coordinate for scroll origin

**Returns:** {object} Scroll result or crash data

**Examples:**
```javascript
// Normal scroll
{"direction": "down", "amount": 100}
// Extreme scroll - test limits
{"direction": "down", "amount": 999999999}
// Negative scroll
{"direction": "up", "amount": -1000}
// Invalid direction - see what happens
{"direction": "diagonal", "amount": 50}
```

---

## POST /cdp/hover

**Function:** `hover_element()`

Hover over element - RAW selector, no validation

**Parameters:**
- `selector ` *(string)*: ANY selector string
- `x` *(number)* *(optional)*: Override X coordinate
- `y` *(number)* *(optional)*: Override Y coordinate

**Returns:** {object} Hover result or crash data

**Examples:**
```javascript
// Normal hover
{"selector": "#menu-item"}
// Malformed selector
{"selector": ">><<invalid>><<"}
// Direct coordinates
{"x": 200, "y": 300}
```

---

## GET /cdp/screenshot

**Function:** `capture_screenshot()`

Capture screenshot of current page - ANY format, ANY quality

**Parameters:**
- `format` *(string)* *(optional)*: Image format (png/jpeg/webp) - no validation
- `quality` *(number)* *(optional)*: Image quality (0-100) - no limits
- `full_page` *(boolean)* *(optional)*: Capture beyond viewport
- `width` *(number)* *(optional)*: Custom viewport width
- `height` *(number)* *(optional)*: Custom viewport height

**Returns:** {binary} Image data or error JSON

**Examples:**
```javascript
// Normal screenshot
GET /cdp/screenshot
// Custom format/quality - no validation
GET /cdp/screenshot?format=webp&quality=999
// Extreme dimensions
GET /cdp/screenshot?width=99999&height=99999&full_page=true
```

---

## POST /cdp/drag

**Function:** `drag_element()`

Drag and drop operation - RAW coordinates

**Parameters:**
- `from_x ` *(number)*: Start X coordinate
- `from_y ` *(number)*: Start Y coordinate
- `to_x ` *(number)*: End X coordinate
- `to_y ` *(number)*: End Y coordinate
- `duration` *(number)* *(optional)*: Drag duration in ms

**Returns:** {object} Drag result or crash data

**Examples:**
```javascript
// Normal drag
{"from_x": 100, "from_y": 200, "to_x": 300, "to_y": 400}
// Extreme coordinates
{"from_x": -999999, "from_y": 999999, "to_x": 0, "to_y": 0}
```

---

