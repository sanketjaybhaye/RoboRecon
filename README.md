[![Author](https://img.shields.io/badge/Author-Sanket%20Jaybhaye-blue)](https://github.com/)
[![Version](https://img.shields.io/badge/Version-6.0-green)]()
[![License](https://img.shields.io/badge/License-Apache-yellow)]()
# 🤖 RoboRecon v6.0 — Smart Recon Upgrade
---

> Advanced Reconnaissance Intelligence Framework  
> Developed by **Sanket Jaybhaye**

---

## 🔍 Overview

This tool is perfect for **bug bounty hunters**, **ethical hackers**, and **pentesters** who need a quick, visual insight into target site structure and crawler restrictions.

---

## ⚙️ Feature
- Fetch and parse `robots.txt` (Allow / Disallow / Sitemap)
- Auto-discover and parse `sitemap.xml` (including `.xml.gz`)
- Recursive sitemap crawling
- Optional URL status scanning (`--scan-urls`)
- Export results in JSON, TXT, CSV, and HTML
- Clean CLI interface with colorized output
- Proxy support (e.g. via TOR)
- Auto-structured reports by domain & timestamp

---

## What’s new in v6.0
- Smart sitemap discovery (checks common sitemap paths automatically)  
- Gzip sitemap support (`*.xml.gz`)  
- Small built-in hidden-path wordlist (fast, low-noise) with multi-threaded checks  
- Automatic JSON, TXT, CSV and optional interactive HTML report generation  
- `--deep` mode runs sitemap discovery + wordlist checks automatically

---

## Requirements
```bash
pip install requests lxml colorama
```

## Quick install (recommended)
```bash
./setup.sh
source .venv/bin/activate
```
___

## Example :
```bash
# Basic run (robots.txt parsing only)
python roboRecon_v6.py -u example.com

# Deep scan: sitemap discovery + hidden path guessing
python roboRecon_v6.py -u example.com --deep --html-report --export-csv --open

# Multi-target from file
python roboRecon_v6.py targets.txt --deep --threads 6
```
## How to use (quick)

1. Save the three files into your RoboRecon folder.
2. chmod +x setup.sh then ./setup.sh
3. source .venv/bin/activate

Run a deep scan:
```bash
python roboRecon_v6.py -u www.python.org --deep --html-report --export-csv --open
```

Notes:

* For Now This is Basic Tool Not Fully Compatible But Good For Start I Hop To Complete it in Future
* `requests[socks]` installs `pysocks` for Tor/SOCKS support.
* `lxml` (or `lxml.etree`) is used for robust sitemap parsing.

---

## License

Apache Version 2.0 License © 2025 Sanket Jaybhaye

---






