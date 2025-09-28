# Advanced DOM API

*Auto-generated from dom_advanced.py JSDoc comments*

## GET/POST /cdp/dom/get_bounds

**Function:** `get_element_bounds()`

Get element bounding box and positioning data

**Parameters:**
- `selector ` *(string)*: Element selector
- `nodeId` *(number)* *(optional)*: Direct node ID (alternative to selector)

**Returns:** {object} Element bounds and positioning data

**Examples:**
```javascript
// Get bounds by selector
GET /cdp/dom/get_bounds?selector=#header
// Get bounds by node ID
POST {"nodeId": 42}
// Malformed selector - test what breaks
GET /cdp/dom/get_bounds?selector=>>>invalid<<<
```

---

## GET/POST /cdp/dom/get_style

**Function:** `get_computed_style()`

Get computed style for element

**Parameters:**
- `selector ` *(string)*: Element selector
- `nodeId` *(number)* *(optional)*: Direct node ID
- `properties` *(array)* *(optional)*: Specific CSS properties to get

**Returns:** {object} Computed style data

**Examples:**
```javascript
// Get all computed styles
GET /cdp/dom/get_style?selector=.container
// Get specific properties
POST {"selector": "#header", "properties": ["color", "font-size", "margin"]}
// Malformed selector
GET /cdp/dom/get_style?selector=>>>bad<<<
```

---

## GET/POST /cdp/dom/is_visible

**Function:** `check_element_visibility()`

Check if element is visible (combines bounds + visibility calculation)

**Parameters:**
- `selector ` *(string)*: Element selector
- `nodeId` *(number)* *(optional)*: Direct node ID
- `strict` *(boolean)* *(optional)*: Strict visibility check (in viewport)

**Returns:** {object} Visibility analysis

**Examples:**
```javascript
// Basic visibility check
GET /cdp/dom/is_visible?selector=#popup
// Strict viewport visibility
POST {"selector": ".hidden-element", "strict": true}
// Check multiple conditions
GET /cdp/dom/is_visible?selector=div&strict=false
```

---

## GET/POST /cdp/dom/shadow

**Function:** `access_shadow_dom()`

Access shadow DOM and describe shadow roots

**Parameters:**
- `selector ` *(string)*: Host element selector
- `nodeId` *(number)* *(optional)*: Direct node ID
- `depth` *(number)* *(optional)*: Shadow tree depth

**Returns:** {object} Shadow DOM structure

**Examples:**
```javascript
// Access shadow DOM
GET /cdp/dom/shadow?selector=custom-element
// Deep shadow tree
POST {"selector": "#shadow-host", "depth": 3}
// Test malformed selector
GET /cdp/dom/shadow?selector=>>>invalid<<<
```

---

## GET/POST /cdp/dom/parent

**Function:** `get_parent_node()`

Get parent node and navigation data

**Parameters:**
- `selector ` *(string)*: Element selector
- `nodeId` *(number)* *(optional)*: Direct node ID
- `siblings` *(boolean)* *(optional)*: Include sibling nodes
- `levels` *(number)* *(optional)*: Number of parent levels to traverse

**Returns:** {object} Parent node data and navigation info

**Examples:**
```javascript
// Get immediate parent
GET /cdp/dom/parent?selector=#child-element
// Get parent with siblings
POST {"selector": ".item", "siblings": true}
// Traverse multiple parent levels
GET /cdp/dom/parent?selector=span&levels=3
```

---

