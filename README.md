[![Author](https://img.shields.io/badge/Author-Sanket%20Jaybhaye-blue)](https://github.com/)
[![Version](https://img.shields.io/badge/Version-1-green)]()
[![License](https://img.shields.io/badge/License-Apache-yellow)]()

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

## 🧩 Installation
Use the included **setup.sh** script to create an isolated environment and install dependencies safely.

```bash
git clone https://github.com/yourname/RoboRecon.git
cd RoboRecon
chmod +x setup.sh
./setup.sh


## Requirements

Recommended inside a virtual environment (Kali-safe):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install requests "requests[socks]" colorama lxml
```

Notes:

* For Now This is Basic Tool Not Fully Compatible But Good For Start I Hop To Complete it in Future
* `requests[socks]` installs `pysocks` for Tor/SOCKS support.
* `lxml` (or `lxml.etree`) is used for robust sitemap parsing.

---

## License

MIT License © 2025 MrRobot

---


