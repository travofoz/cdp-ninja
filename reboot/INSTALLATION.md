# CDP-Ninja Mass Screenshot - Complete Installation Guide

For **@UK_Daniel_Card** (@mRr3b00t)

## Quick Start (Local Setup)

If you're running everything on the same machine - this is the easiest way:

### 1. Install CDP-Ninja

```bash
# Clone the repo
git clone https://github.com/travofoz/cdp-ninja.git
cd cdp-ninja

# Install dependencies
npm install

# Start CDP-Ninja
npm start
```

CDP-Ninja will start on `http://localhost:8888` by default.

### 2. Install Python Dependencies

```bash
pip install requests
```

### 3. Create Your Domain List

```bash
# Create domains.txt with one domain per line
cat > domains.txt << EOF
google.com
github.com
stackoverflow.com
example.org
EOF
```

### 4. Run Mass Screenshot

```bash
cd reboot/
python3 mass_screenshot.py
```

Done! Check the `output/` folder for results.

---

## Advanced Setup (Remote/Tunnel)

If CDP-Ninja is running on a remote server or you need tunnel access:

### Option A: SSH Tunnel (Recommended)

**On your local machine:**

```bash
# Forward remote CDP-Ninja to local port
ssh -L 8888:localhost:8888 user@remote-server

# In another terminal, run the script normally
python3 mass_screenshot.py
```

**On the remote server:**
```bash
# Start CDP-Ninja normally
cd cdp-ninja
npm start
```

### Option B: Direct Remote Access

Modify the script for direct remote access:

```python
# Edit mass_screenshot.py, change this line:
base_url = "http://your-remote-server:8888"
```

**Security Warning:** Only do this if the remote server is properly secured!

### Option C: VPN Access

If you're using a VPN to access the remote network:

```bash
# Connect to VPN first
# Then run normally - CDP-Ninja should be accessible via VPN IP
python3 mass_screenshot.py
```

---

## Installation Troubleshooting

### CDP-Ninja Won't Start

```bash
# Check if Chrome is installed
google-chrome --version

# Install Chrome on Ubuntu/Debian
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb https://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install google-chrome-stable

# Install Chrome on CentOS/RHEL
wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
sudo yum localinstall google-chrome-stable_current_x86_64.rpm
```

### Python Issues

```bash
# Make sure you have Python 3.6+
python3 --version

# Install pip if missing
sudo apt install python3-pip  # Ubuntu/Debian
sudo yum install python3-pip  # CentOS/RHEL

# Install requests
pip3 install requests
```

### Permission Issues

```bash
# Make script executable
chmod +x mass_screenshot.py

# Run with explicit python3
python3 mass_screenshot.py
```

---

## Usage Examples

### Basic Usage

```bash
# Use default domains.txt, 5 second delay
python3 mass_screenshot.py
```

### Custom Domains File

```bash
# Use your own domain list
python3 mass_screenshot.py my_targets.txt
```

### Custom Delay

```bash
# Wait 10 seconds for slow-loading pages
python3 mass_screenshot.py domains.txt 10
```

### Batch Processing Different Lists

```bash
# Process multiple domain lists
python3 mass_screenshot.py high_priority.txt 3
python3 mass_screenshot.py standard.txt 5
python3 mass_screenshot.py slow_sites.txt 15
```

---

## Output Structure Explained

```
output/
├── google_com/                 # Domain with dots/colons replaced
│   ├── screenshot.png         # Visual capture of rendered page
│   ├── source.html           # Final HTML after JS execution
│   └── metadata.json         # Timestamp, settings used
├── github_com/
│   ├── screenshot.png
│   ├── source.html
│   └── metadata.json
└── malicious_site_com/
    ├── screenshot.png         # Even if site tries to block
    ├── source.html           # Complete DOM after execution
    └── metadata.json         # Forensic metadata
```

---

## Security Considerations

### Why This is Better Than Curl

1. **Full JavaScript Execution** - Malware/trackers run as intended
2. **Client-Side Fingerprinting** - Triggers proper browser detection
3. **Dynamic Content** - AJAX, WebSocket, real-time updates captured
4. **Visual Evidence** - Screenshots prove what actually rendered
5. **Complete DOM** - Gets final HTML after all modifications

### Defensive Research Use Cases

- **Phishing Analysis** - See what victims actually see
- **Malware Research** - Capture full infection chain
- **Brand Protection** - Monitor copycat sites visually
- **Compliance Auditing** - Document actual site behavior
- **Threat Intelligence** - Automated reconnaissance with proof

### Safety Tips

- Run in isolated VM/container
- Use VPN for sensitive targets
- Monitor network traffic during scans
- Review output before sharing
- Consider legal implications of automated scanning

---

## Performance Tuning

### For Large Domain Lists

```python
# Modify these values in mass_screenshot.py:
delay = 3           # Faster for simple pages
timeout = 15        # Shorter timeout for unresponsive sites
sleep(0.5)         # Reduce pause between requests
```

### For High-Value Targets

```python
delay = 10          # Longer wait for complex pages
timeout = 60        # Patient with slow sites
sleep(2)           # More respectful timing
```

---

## Contact

Built by **CYTO** for **@UK_Daniel_Card** and the security research community.

- CDP-Ninja Repo: https://github.com/travofoz/cdp-ninja
- Issues/Features: Open GitHub issues
- Security Research: Use responsibly and ethically

**Happy hunting! 🔍**