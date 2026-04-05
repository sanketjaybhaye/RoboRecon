[![Author](https://img.shields.io/badge/Author-Sanket%20Jaybhaye-blue)](https://github.com/sanketjaybhaye)
[![Enhanced by](https://img.shields.io/badge/Enhanced%20by-Elliot-red)](https://github.com/)
[![Version](https://img.shields.io/badge/Version-8.0%20ULTIMATE-purple)]()
[![License](https://img.shields.io/badge/License-Apache-yellow)]()

# 🤖 RoboRecon v8.0 ULTIMATE — Elite Hacker Reconnaissance Framework

---

> **Professional-grade, multi-stage reconnaissance framework for bug bounty hunters, ethical hackers, and penetration testers.**
>
> **20 modules** | **4 profiles** | **SQLite tracking** | **Interactive dashboards**
>
> Original by **Sanket Jaybhaye** | Enhanced by **Elliot**

---

## 🔍 What Changed from v7.0 → v8.0

| Feature | v7.0 | v8.0 |
|---------|------|------|
| Modules | 13 | **20** |
| Screenshot capture | ❌ (planned) | ✅ DrissionPage |
| Email harvesting | ❌ | ✅ Regex + page crawling |
| Cloud bucket detection | ❌ | ✅ S3/Azure/GCS enumeration |
| GraphQL detection | ❌ | ✅ Introspection checks |
| Git exposure checks | ❌ | ✅ .git folder scanning |
| Parameter discovery | ❌ | ✅ Form/URL param extraction |
| Rate limiting detection | ❌ | ✅ 10-request burst test |
| API key scanning | Partial (JS only) | ✅ Full page + headers |
| Whois lookup | ❌ | ✅ Registrar/dates/NS |
| crt.sh integration | ❌ | ✅ Certificate transparency |
| HTML dashboard | Basic | ✅ Alerts, cards, filters |

---

## ⚙️ 20 Reconnaissance Modules

| # | Module | Tools/APIs | Purpose |
|---|--------|-----------|---------|
| 1 | **Subdomain Enumeration** | subfinder, amass, crt.sh | Passive subdomain discovery from 3 sources |
| 2 | **DNS Reconnaissance** | dig | A/AAAA/MX/NS/TXT + SPF/DMARC + zone transfers |
| 3 | **Port Scanning** | nmap | Top 100 ports with service detection |
| 4 | **Technology Fingerprinting** | whatweb, wafw00f | Server, CMS, framework, WAF identification |
| 5 | **Directory Brute-Forcing** | Built-in (threaded) | Multi-tier wordlists (70/180/250 paths) |
| 6 | **Vulnerability Scanning** | nuclei | Automated vuln scanning with community templates |
| 7 | **JavaScript Analysis** | Built-in regex | Extract API endpoints + secrets from JS files |
| 8 | **Screenshot Capture** | DrissionPage | Visual recon of target + subdomains |
| 9 | **Wayback Machine Mining** | web.archive.org API | Historical URL discovery |
| 10 | **SSL/TLS Analysis** | openssl, testssl.sh | Cert expiry, SANs, protocol support |
| 11 | **Subdomain Takeover** | Built-in fingerprints | GitHub Pages, S3, Heroku, Azure, Shopify, etc. |
| 12 | **Email Harvesting** | Built-in regex | Extract emails from pages + contact/about/team |
| 13 | **Cloud Bucket Detection** | Built-in | S3, Azure Blob, GCS, DigitalOcean Spaces checks |
| 14 | **GraphQL Detection** | Built-in | Endpoint discovery + introspection testing |
| 15 | **Git Exposure** | Built-in | .git folder, HEAD, config, refs exposure |
| 16 | **Parameter Discovery** | Built-in | Form inputs, URL params, API parameters |
| 17 | **Rate Limiting** | Built-in burst test | 10-request rapid-fire test for 429 responses |
| 18 | **API Key Scanning** | Built-in regex | AWS, Google, GitHub, Slack, JWT tokens in HTML/headers |
| 19 | **Whois Lookup** | whois | Registrar, creation/expiry dates, nameservers |
| 20 | **Robots.txt + Sitemap** | Built-in | Enhanced parsing with smart sitemap discovery |

---

## 📦 Installation

### Quick Setup (Recommended)
```bash
cd /home/kali/Downloads/RoboRecon
chmod +x steup.sh
./steup.sh
source .venv/bin/activate
```

### Manual Install
```bash
# System tools (Kali/Debian)
sudo apt-get install -y subfinder amass nmap whatweb wafw00f \
    gobuster ffuf dnsutils nuclei httpx openssl jq testssl.sh

# Python dependencies
pip install requests lxml colorama DrissionPage
```

---

## 🚀 Usage

### Quick Scan (~5s)
Robots.txt + sitemap only.
```bash
python3 RoboRecon.py -u example.com --profile quick --html-report
```

### Standard Scan (~1-2min) ✅ Recommended
Subdomains, DNS, wayback, JS analysis, email harvesting, cloud buckets, GraphQL, git checks, parameter discovery, rate limiting, API key scanning.
```bash
python3 RoboRecon.py -u example.com --profile standard --html-report --open
```

### Deep Scan (~3-5min)
Standard + port scan, vuln scan, subdomain takeover, SSL/TLS, whois.
```bash
python3 RoboRecon.py -u example.com --profile deep --html-report --export-csv --threads 15
```

### Nuclear Scan (~5-15min)
Deep + directory brute-force (250 paths), screenshots of target + subdomains.
```bash
python3 RoboRecon.py -u example.com --profile nuclear --html-report --open
```

### Multi-Target
```bash
python3 RoboRecon.py targets.txt --profile deep --threads 10
```

### Through Proxy (Tor)
```bash
python3 RoboRecon.py -u example.com --profile standard --proxy socks5h://127.0.0.1:9050
```

### List Modules
```bash
python3 RoboRecon.py --list-modules
```

---

## 📊 Recon Profiles

| Profile | Modules | Duration | Best For |
|---------|---------|----------|----------|
| **quick** | sitemap, robots | ~5s | Fast checks |
| **standard** | quick + 12 modules | ~1-2min | Daily recon |
| **deep** | standard + 5 modules | ~3-5min | Bug bounty assessment |
| **nuclear** | deep + brute-force + screenshots | ~5-15min | Full penetration test prep |

---

## 📁 Output Structure

```
recon_reports/
├── example.com/
│   └── 20260405_050000/
│       ├── report.json      # Full structured data (machine-readable)
│       ├── report.txt       # Human-readable summary
│       ├── report.html      # Interactive dark-themed dashboard
│       └── urls.csv         # Discovered URLs (--export-csv)
├── screenshot_*.png         # Visual recon captures
└── robocon.db               # SQLite database (all historical scans)
```

---

## 🖥️ HTML Dashboard Features

- **Dark theme** — Easy on the eyes during long sessions
- **Summary cards** — At-a-glance metrics (subdomains, ports, vulns, emails, secrets)
- **Critical alerts** — Red-highlighted findings (exposed git, API keys, takeover vulns)
- **Sortable tables** — Click column headers to sort
- **Filter inputs** — Real-time filtering of subdomains and paths
- **Responsive layout** — Works on mobile too

---

## ⚠️ Legal Disclaimer

This tool is designed for **ethical hacking, bug bounty hunting, and authorized penetration testing only**. Always obtain explicit written authorization before scanning any target. The authors assume **no liability** for misuse or unauthorized use.

---

## 📝 Changelog

### v8.0 ULTIMATE (Current)
- **20 modules** (up from 13)
- Screenshot capture via DrissionPage
- Email harvesting from web pages
- Cloud bucket detection (S3/Azure/GCS/DO Spaces)
- GraphQL introspection detection
- Git exposure checks (.git folder, HEAD, config)
- Parameter discovery (forms, URL params, API params)
- Rate limiting detection (burst test)
- API key scanning (AWS, Google, GitHub, Slack, JWT, etc.)
- Whois lookup (registrar, dates, NS)
- crt.sh integration for subdomain enumeration
- Enhanced HTML dashboard with critical alerts and filters
- Tiered wordlists: SMALL (70), MEDIUM (180), LARGE (250)

### v7.0 PRO
- 13 reconnaissance modules
- SQLite database for historical tracking
- 4 recon profiles
- Interactive HTML dashboard

### v6.0 (Original)
- Smart sitemap discovery
- Hidden path wordlist
- HTML report generation

---

## 📜 License

Apache License 2.0 © 2026 Sanket Jaybhaye

---

> *"Reconnaissance is 80% of the battle. The other 20% is knowing what to do with it."*
> — Every hacker, ever
