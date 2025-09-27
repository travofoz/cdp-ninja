#!/usr/bin/env python3
"""
CDP-Ninja Mass Screenshot Tool
For @UK_Daniel_Card (@mRr3b00t)

Reads domains from file, visits each page, takes screenshot after delay,
saves source to sensible folder structure, then moves to next domain.

Requires CDP-Ninja running locally on port 8888.
"""

import requests
import time
import os
import base64
import json
from urllib.parse import urlparse
from pathlib import Path

def mass_screenshot(domains_file="domains.txt", delay=5, output_dir="output"):
    """
    Process list of domains - screenshot and save source for each

    Args:
        domains_file: Text file with one domain per line
        delay: Seconds to wait after page load before screenshot
        output_dir: Base directory for saving results
    """
    base_url = "http://localhost:8888"

    # Ensure output directory exists
    Path(output_dir).mkdir(exist_ok=True)

    if not os.path.exists(domains_file):
        print(f"❌ Domain file '{domains_file}' not found!")
        print("Create domains.txt with one domain per line, e.g.:")
        print("  google.com")
        print("  github.com")
        print("  example.org")
        return

    print(f"🚀 Starting mass screenshot with {delay}s delay...")
    print(f"📂 Output directory: {output_dir}")
    print("=" * 50)

    with open(domains_file, 'r') as f:
        domains = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    total = len(domains)
    for i, domain in enumerate(domains, 1):
        # Ensure proper URL format
        url = f"https://{domain}" if not domain.startswith(('http://', 'https://')) else domain
        parsed = urlparse(url)
        safe_name = parsed.netloc.replace('.', '_').replace(':', '_')

        print(f"[{i}/{total}] Processing: {url}")

        try:
            # Navigate to page
            print("  🌐 Navigating...")
            nav_resp = requests.post(f"{base_url}/cdp/navigate",
                                   json={"url": url},
                                   timeout=30)

            if not nav_resp.ok:
                print(f"  ❌ Navigation failed: {nav_resp.status_code}")
                continue

            # Wait for page load
            print(f"  ⏳ Waiting {delay}s for page load...")
            time.sleep(delay)

            # Create domain-specific output directory
            domain_dir = Path(output_dir) / safe_name
            domain_dir.mkdir(exist_ok=True)

            # Take screenshot
            print("  📸 Taking screenshot...")
            screenshot_resp = requests.post(f"{base_url}/cdp/screenshot", timeout=30)

            if screenshot_resp.ok:
                result = screenshot_resp.json()
                screenshot_data = result.get('screenshot', '')
                if screenshot_data:
                    screenshot_path = domain_dir / "screenshot.png"
                    with open(screenshot_path, 'wb') as img:
                        img.write(base64.b64decode(screenshot_data))
                    print(f"  ✅ Screenshot: {screenshot_path}")
                else:
                    print("  ⚠️  Screenshot data empty")
            else:
                print(f"  ❌ Screenshot failed: {screenshot_resp.status_code}")

            # Get page source
            print("  📄 Saving page source...")
            source_resp = requests.post(f"{base_url}/cdp/execute",
                                      json={"code": "document.documentElement.outerHTML"},
                                      timeout=30)

            if source_resp.ok:
                result = source_resp.json()
                source_data = result.get('result', {}).get('result', {}).get('value', '')
                if source_data:
                    source_path = domain_dir / "source.html"
                    with open(source_path, 'w', encoding='utf-8') as src:
                        src.write(source_data)
                    print(f"  ✅ Source: {source_path}")
                else:
                    print("  ⚠️  Source data empty")
            else:
                print(f"  ❌ Source failed: {source_resp.status_code}")

            # Save metadata
            metadata = {
                "url": url,
                "domain": domain,
                "timestamp": time.time(),
                "delay_used": delay
            }
            metadata_path = domain_dir / "metadata.json"
            with open(metadata_path, 'w') as meta:
                json.dump(metadata, meta, indent=2)

        except requests.exceptions.Timeout:
            print(f"  ❌ Timeout processing {url}")
        except Exception as e:
            print(f"  ❌ Error processing {url}: {e}")

        print("")  # Blank line for readability
        time.sleep(1)  # Brief pause between requests

    print("🏁 Mass screenshot complete!")

if __name__ == "__main__":
    import sys

    # Simple CLI argument handling
    domains_file = sys.argv[1] if len(sys.argv) > 1 else "domains.txt"
    delay = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    print("CDP-Ninja Mass Screenshot Tool")
    print("For security research and web analysis")
    print("")

    mass_screenshot(domains_file, delay)