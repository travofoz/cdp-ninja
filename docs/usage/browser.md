# Browser Interaction Domain API

Core browser interactions: click, type, scroll, hover, drag, screenshots.

## Click Operations

### POST /cdp/click
Click on elements by selector or coordinates.

**By Selector:**
```json
{
  "selector": "#submit-button"
}
```

**By Coordinates:**
```json
{
  "x": 500,
  "y": 300
}
```

**Example:**
```bash
curl -X POST http://localhost:8888/cdp/click \
  -H "Content-Type: application/json" \
  -d '{"selector": "button[type=submit]"}'
```

## Text Input

### POST /cdp/type
Type text into focused element or specific selector.

**Request:**
```json
{
  "text": "Hello World",
  "selector": "#username"  // optional - focuses element first
}
```

**Example:**
```bash
curl -X POST http://localhost:8888/cdp/type \
  -H "Content-Type: application/json" \
  -d '{"text": "test@example.com", "selector": "#email"}'
```

## Page Scrolling

### POST /cdp/scroll
Scroll the page in specified direction.

**Request:**
```json
{
  "direction": "down",  // "up", "down"
  "amount": 500        // pixels
}
```

## Mouse Hover

### POST /cdp/hover
Hover over element by selector.

**Request:**
```json
{
  "selector": ".menu-item"
}
```

## Drag Operations

### POST /cdp/drag
Drag from start to end coordinates or selectors.

**Coordinate Drag:**
```json
{
  "startX": 100,
  "startY": 200,
  "endX": 300,
  "endY": 400
}
```

**Selector Drag:**
```json
{
  "startSelector": "#draggable",
  "endSelector": "#dropzone"
}
```

## Screenshots

### GET /cdp/screenshot
Capture page screenshot.

**Parameters:**
- `format`: `png` (default), `jpeg`
- `quality`: 1-100 (JPEG only)
- `full_page`: `true`/`false`

**Example:**
```bash
curl http://localhost:8888/cdp/screenshot?format=png&full_page=true > screenshot.png
```

## Integration Examples

**Login Workflow:**
```bash
# Navigate to login page
curl -X POST http://localhost:8888/cdp/page/navigate \
  -d '{"url": "https://example.com/login"}'

# Fill username
curl -X POST http://localhost:8888/cdp/type \
  -d '{"text": "user@example.com", "selector": "#username"}'

# Fill password
curl -X POST http://localhost:8888/cdp/type \
  -d '{"text": "password123", "selector": "#password"}'

# Click submit
curl -X POST http://localhost:8888/cdp/click \
  -d '{"selector": "button[type=submit]"}'

# Take screenshot
curl http://localhost:8888/cdp/screenshot > result.png
```