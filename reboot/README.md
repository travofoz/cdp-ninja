# CDP-Ninja Mass Screenshot Tool

For **@UK_Daniel_Card** (@mRr3b00t) - automated domain screenshotting and source saving.

## What it does

- Reads domains from a text file
- Visits each page with a real browser (via CDP-Ninja)
- Waits X seconds for full page load
- Takes a screenshot
- Saves the page source
- Creates organized folder structure
- Moves to next domain

Perfect for security research where you need full client-side interaction vs curl.

## Setup

1. **Start CDP-Ninja locally:**
   ```bash
   # In your CDP-Ninja directory
   npm start
   # Should be running on localhost:8888
   ```

2. **Create your domains file:**
   ```bash
   echo "google.com" > domains.txt
   echo "github.com" >> domains.txt
   echo "example.org" >> domains.txt
   ```

3. **Run the script:**
   ```bash
   python3 mass_screenshot.py
   ```

## Usage

Basic usage (5 second delay):
```bash
python3 mass_screenshot.py
```

Custom domains file and delay:
```bash
python3 mass_screenshot.py my_domains.txt 10
```

## Output Structure

```
output/
├── google_com/
│   ├── screenshot.png
│   ├── source.html
│   └── metadata.json
├── github_com/
│   ├── screenshot.png
│   ├── source.html
│   └── metadata.json
└── example_org/
    ├── screenshot.png
    ├── source.html
    └── metadata.json
```

## Why This vs Curl

- **Full JavaScript execution** - Gets the page as users see it
- **Dynamic content** - Captures AJAX-loaded content
- **Real browser fingerprint** - Triggers client-side security properly
- **Screenshots** - Visual proof of what was rendered
- **Complete DOM** - Gets the final HTML after all JS modifications

Perfect for security testing where you need to see how pages actually behave with full client interaction.

## Configuration

Edit the script to customize:
- Default delay (currently 5 seconds)
- Output directory structure
- Screenshot format/quality
- Error handling behavior
- Timeout values

## Requirements

- Python 3.6+
- CDP-Ninja running locally
- `requests` library (`pip install requests`)

## Notes

- Designed for local use (no tunnel complexity)
- Handles HTTPS automatically
- Safe domain name sanitization for folders
- Comprehensive error handling and logging
- Metadata tracking for forensics

Built with ❤️ by CYTO for the security community.