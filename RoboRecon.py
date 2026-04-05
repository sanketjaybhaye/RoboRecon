#!/usr/bin/env python3
"""
RoboRecon v8.0 ULTIMATE - Elite Hacker Reconnaissance Framework
================================================================
Author: Sanket Jaybhaye
Enhanced by: Elliot

Modules (20):
  1.  Subdomain Enumeration (subfinder, amass, crt.sh, Rapiddns)
  2.  DNS Reconnaissance (A/AAAA/MX/NS/TXT/SPF/DMARC, zone transfers)
  3.  Port Scanning (nmap, masscan top ports)
  4.  Technology Fingerprinting (whatweb, wafw00f, server headers)
  5.  Directory Brute-Forcing (gobuster/ffuf with tiered wordlists)
  6.  Vulnerability Scanning (nuclei templates)
  7.  JavaScript Analysis (endpoints, API keys, secrets extraction)
  8.  Screenshot Capture (DrissionPage/undetected-chromedriver)
  9.  Wayback Machine Mining (historical URLs)
  10. SSL/TLS Analysis (cert expiry, SANs, cipher suites)
  11. Subdomain Takeover Detection (GitHub Pages, S3, Heroku, Azure)
  12. Email Harvesting (extract emails from web pages)
  13. Cloud Bucket Detection (S3, Azure Blob, GCS misconfigs)
  14. GraphQL Detection (introspection, endpoint discovery)
  15. Git Exposure (.git folder checks, commit leaks)
  16. Parameter Discovery (hidden URL parameters)
  17. Rate Limiting Detection (response analysis)
  18. API Key Scanning (headers, HTML, JS, responses)
  19. Whois & Registration Data
  20. Robots.txt + Sitemap Crawling (enhanced with smart discovery)

Output: JSON, TXT, CSV, HTML dashboard (dark-themed, interactive)
Database: SQLite for historical tracking
"""
import argparse, os, re, json, time, random, threading, csv, webbrowser, io, gzip, html as html_module, sys, sqlite3, subprocess, socket, ssl, ipaddress, urllib.parse
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urljoin, urlencode, parse_qs
from collections import defaultdict
import hashlib, base64

try:
    import requests
    from lxml import etree
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run: pip install requests lxml colorama")
    raise

# Lazy import for optional screenshot module
try:
    from DrissionPage import ChromiumPage, ChromiumOptions
    HAS_DRIPAGE = True
except ImportError:
    HAS_DRIPAGE = False

# ─── Configuration ───────────────────────────────────────────────────────────
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
BASE_OUTPUT = "recon_reports"
DB_PATH = os.path.join(BASE_OUTPUT, "robocon.db")
os.makedirs(BASE_OUTPUT, exist_ok=True)
lock = threading.Lock()
progress = {"total": 20, "done": 0, "current": ""}

# ─── Wordlists ───────────────────────────────────────────────────────────────
SMALL_WORDLIST = [
    "admin/", "administrator/", "login", "user/login", "wp-admin/", "cpanel/", "panel/",
    "backup.zip", "backup.tar.gz", "db_backup.sql", "uploads/", "dev/", "test/", "old/", "staging/",
    ".git/", ".gitignore", ".env", "config.php", "config.yml", "config.json", "wp-config.php",
    "phpinfo.php", "info.php", "debug/", "console/", "api/", "api/v1/", "api/v2/",
    "swagger/", "swagger.json", "graphql", "graphiql", "phpmyadmin/", "pma/",
    "server-status", "server-info", "sitemap.xml", "robots.txt", ".htaccess",
    "web.config", "crossdomain.xml", "clientaccesspolicy.xml", "composer.json",
    "package.json", "webpack.config.js", "Dockerfile", "docker-compose.yml",
    ".aws/credentials", ".kube/config", "id_rsa", "id_dsa", "known_hosts",
    "backup.sql", "dump.sql", "database.sql", "data.sql", "db.sql",
    "logs/", "error.log", "access.log", ".log", "temp/", "tmp/",
    "index.php.bak", "index.html.bak", "config.bak", "wp-content/uploads/",
    "shell.php", "cmd.php", "r57.php", "c99.php", "b374k.php"
]

MEDIUM_WORDLIST = SMALL_WORDLIST + [
    "cgi-bin/", "includes/", "modules/", "templates/", "cache/", "lib/",
    "inc/", "classes/", "assets/", "images/", "img/", "css/", "js/",
    "scripts/", "styles/", "fonts/", "downloads/", "files/",
    "docs/", "documentation/", "wiki/", "forum/", "blog/",
    "shop/", "store/", "cart/", "checkout/", "payment/",
    "dashboard/", "settings/", "profile/", "account/", "users/",
    "register/", "signup/", "forgot-password", "reset-password",
    "oauth/", "oauth2/", "token/", "auth/", "authentication/",
    "webhook/", "webhooks/", "callback/", "notifications/",
    "metrics/", "health", "healthcheck", "status", "ping",
    "actuator/", "actuator/env", "actuator/health", "actuator/info",
    ".well-known/", ".well-known/security.txt", ".well-known/csp-violation-report",
    "elmah.axd", "trace.axd", "default.aspx", "index.asp",
    "xmlrpc.php", "wp-json/", "wp-includes/", "wp-content/plugins/",
    "manager/html", "jmx-console/", "web-console/", "invoker/",
    "jenkins/", "hudson/", "teamcity/", "bamboo/",
    "sonarqube/", "kibana/", "grafana/", "prometheus/",
    "elastic/", "elasticsearch/", "mongo/", "mongodb/",
    "redis/", "memcached/", "rabbitmq/", "kafka/",
    "zabbix/", "nagios/", "cacti/", "splunk/",
    "confluence/", "jira/", "bitbucket/", "gitlab/",
    "gitea/", "redmine/", "phabricator/", "taiga/"
]

LARGE_WORDLIST = MEDIUM_WORDLIST + [
    "admin.php", "login.php", "shell.php", "cmd.php", "upload.php",
    "index.php.swp", ".DS_Store", ".htpasswd", ".htgroup",
    "debug.php", "test.php", "php.php", "cmd.asp", "shell.asp",
    "/cgi-bin/test", "/cgi-bin/test-cgi", "/cgi-bin/php",
    "/cgi-bin/php5", "/cgi-bin/php-cgi", "/cgi-bin/php.cgi",
    "admin.php?login", "admin.html", "login.html", "login.htm",
    "manager/", "console/", "terminal/", "command/",
    "wp-login.php", "wp-cron.php", "xmlrpc.php",
    ".svn/", ".svn/entries", ".bzr/", ".hg/",
    "composer.lock", "yarn.lock", "Gemfile.lock",
    "README.md", "CHANGELOG.md", "LICENSE.txt",
    "backup.tar", "backup.gz", "backup.zip", "backup.7z",
    "dump.tar.gz", "dump.zip", "site.tar.gz", "www.tar.gz",
    "config.ini", "config.xml", "config.properties",
    "database.yml", "database.ini", "settings.py",
    ".git/config", ".git/HEAD", ".git/FETCH_HEAD",
    ".env.local", ".env.production", ".env.development",
    "server.xml", "web.xml", "context.xml",
    "phpmyadmin/index.php", "pMA/index.php",
    "solr/", "jenkins/script", "jenkins/console",
    "struts", "weblogic", "jboss/", "tomcat/",
    "actuator/mappings", "actuator/trace", "actuator/loggers",
    ".git/objects/", ".git/refs/", ".git/description",
    "cgi-bin/admin.cgi", "cgi-bin/login.cgi",
    "aspnet_client/", "web.config.bak",
    "phpinfo.php.bak", "info.php.bak",
    "debug.txt", "debug.log", "debug.html"
]

COMMON_SITEMAP_LOCATIONS = [
    "/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml",
    "/sitemap.xml.gz", "/sitemap_index.xml.gz", "/sitemap.txt",
    "/sitemap/sitemap.xml", "/main-sitemap.xml"
]

SUBDOMAIN_TAKEOVER_FINGERPRINTS = [
    {"service": "GitHub Pages", "cnames": ["github.io"], "fingerprint": ["There isn't a GitHub Pages site here.", "For root URLs"]},
    {"service": "Heroku", "cnames": ["herokuapp.com"], "fingerprint": ["No such app", "is not a recognized application"]},
    {"service": "AWS S3", "cnames": ["amazonaws.com"], "fingerprint": ["NoSuchBucket", "The specified bucket does not exist"]},
    {"service": "Azure", "cnames": ["azurewebsites.net", "cloudapp.azure.com"], "fingerprint": ["404 Web Site not found", "Web App not found"]},
    {"service": "Shopify", "cnames": ["myshopify.com"], "fingerprint": ["Sorry, this shop is currently unavailable"]},
    {"service": "WordPress.com", "cnames": ["wordpress.com"], "fingerprint": ["Do you want to register", "wordpress.com/checkout/"]},
    {"service": "Pantheon", "cnames": ["pantheonsite.io"], "fingerprint": ["The gods are wise", "404 error"]},
    {"service": "Tumblr", "cnames": ["tumblr.com"], "fingerprint": ["There's nothing here.", "Whatever you were looking for doesn't currently exist"]},
    {"service": "Surge", "cnames": ["surge.sh"], "fingerprint": ["project not found", "This Surge site has not been configured"]},
    {"service": "Netlify", "cnames": ["netlify.app", "netlify.com"], "fingerprint": ["Page Not Found", "not found"]}
]

JS_ENDPOINT_PATTERNS = [
    r'["\'](/api/[^"\']+)["\']',
    r'["\'](/v\d+/[^"\']+)["\']',
    r'["\'](/graphql[^"\']*)["\']',
    r'["\'](/rest/[^"\']+)["\']',
    r'fetch\s*\(\s*["\']([^"\']+)["\']',
    r'axios\.(get|post|put|delete)\s*\(\s*["\']([^"\']+)["\']',
    r'url\s*:\s*["\']([^"\']+)["\']'
]

JS_SECRET_PATTERNS = [
    (r'(?:api[_-]?key|apikey)\s*[:=]\s*["\']([a-zA-Z0-9_\-]{20,})["\']', "API Key"),
    (r'(?:secret|token|password|passwd)\s*[:=]\s*["\']([a-zA-Z0-9_\-]{10,})["\']', "Secret/Token"),
    (r'(?:aws[_-]?access[_-]?key[_-]?id|aws[_-]?secret[_-]?access[_-]?key)\s*[:=]\s*["\']([A-Z0-9/+=]{20,})["\']', "AWS Credentials"),
    (r'(?:private[_-]?key)\s*[:=]\s*["\']([a-zA-Z0-9_\-]{20,})["\']', "Private Key"),
    (r'(?:bearer|authorization)\s*[:=]\s*["\']([a-zA-Z0-9_\-\.]{20,})["\']', "Bearer Token"),
    (r'(?:stripe[_-]?key)\s*[:=]\s*["\']([a-zA-Z0-9_\-]{20,})["\']', "Stripe Key"),
    (r'(?:sendgrid|sg[_-]?key)\s*[:=]\s*["\']([a-zA-Z0-9_\-]{20,})["\']', "SendGrid Key"),
    (r'(?:firebase[_-]?key)\s*[:=]\s*["\']([a-zA-Z0-9_\-]{20,})["\']', "Firebase Key"),
]

CLOUD_BUCKET_PATTERNS = [
    (r'(?:s3\.amazonaws\.com|amazonaws\.com)/([a-zA-Z0-9.\-_]+)', "AWS S3"),
    (r'(?:storage\.cloud\.google\.com|storage\.googleapis\.com)/([a-zA-Z0-9.\-_]+)', "Google Cloud Storage"),
    (r'(?:blob\.core\.windows\.net)/([a-zA-Z0-9.\-_]+)', "Azure Blob Storage"),
    (r'(?:digitaloceanspaces\.com)/([a-zA-Z0-9.\-_]+)', "DigitalOcean Spaces"),
]

EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

TEMPLATE_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Inter', 'Segoe UI', system-ui, sans-serif; background: #0d1117; color: #c9d1d9; padding: 24px; }
.container { max-width: 1400px; margin: auto; }
h1 { font-size: 28px; color: #58a6ff; margin-bottom: 8px; }
h2 { font-size: 20px; color: #58a6ff; margin: 24px 0 12px; padding-bottom: 8px; border-bottom: 1px solid #30363d; }
h3 { font-size: 16px; color: #79c0ff; margin: 16px 0 8px; }
.meta { font-size: 13px; color: #8b949e; margin-bottom: 20px; }
.summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin: 20px 0; }
.card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; text-align: center; }
.card .number { font-size: 32px; font-weight: bold; color: #58a6ff; }
.card .label { font-size: 13px; color: #8b949e; margin-top: 4px; }
table { width: 100%; border-collapse: collapse; margin: 12px 0; background: #161b22; border-radius: 8px; overflow: hidden; }
th, td { padding: 10px 14px; border-bottom: 1px solid #21262d; text-align: left; font-size: 14px; }
th { background: #1c2128; color: #8b949e; font-weight: 600; cursor: pointer; user-select: none; }
th:hover { background: #252a30; }
tr:hover { background: #1c2128; }
a { color: #58a6ff; text-decoration: none; }
a:hover { text-decoration: underline; }
pre { background: #161b22; padding: 16px; border-radius: 8px; overflow: auto; font-size: 13px; line-height: 1.5; border: 1px solid #30363d; }
code { background: #1f2428; padding: 2px 6px; border-radius: 4px; font-size: 13px; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; margin-right: 4px; }
.badge-green { background: #238636; color: #fff; }
.badge-red { background: #da3633; color: #fff; }
.badge-yellow { background: #d29922; color: #000; }
.badge-blue { background: #1f6feb; color: #fff; }
.badge-gray { background: #484f58; color: #fff; }
.section { margin: 24px 0; }
.alert { padding: 12px 16px; border-radius: 6px; margin: 8px 0; border-left: 4px solid; }
.alert-critical { background: #2d1b1b; border-color: #f85149; color: #f85149; }
.alert-high { background: #2d2615; border-color: #d29922; color: #d29922; }
.alert-info { background: #0d1b2a; border-color: #58a6ff; color: #58a6ff; }
.filter-input { width: 100%; padding: 10px; margin-bottom: 12px; background: #161b22; border: 1px solid #30363d; color: #c9d1d9; border-radius: 6px; font-size: 14px; }
.filter-input:focus { outline: none; border-color: #58a6ff; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 900px) { .grid-2 { grid-template-columns: 1fr; } }
"""

TEMPLATE_JS = """
function sortTable(n, id) {
  var table = document.getElementById(id), rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
  switching = true; dir = "asc";
  while (switching) {
    switching = false; rows = table.rows;
    for (i = 1; i < (rows.length - 1); i++) {
      shouldSwitch = false;
      x = rows[i].getElementsByTagName("TD")[n];
      y = rows[i + 1].getElementsByTagName("TD")[n];
      if (dir == "asc") { if (x.innerText.toLowerCase() > y.innerText.toLowerCase()) { shouldSwitch = true; break; } }
      else { if (x.innerText.toLowerCase() < y.innerText.toLowerCase()) { shouldSwitch = true; break; } }
    }
    if (shouldSwitch) { rows[i].parentNode.insertBefore(rows[i + 1], rows[i]); switching = true; switchcount++; }
    else { if (switchcount == 0 && dir == "asc") { dir = "desc"; switching = true; } }
  }
}
function filterTable(inputId, tableId) {
  var filter = document.getElementById(inputId).value.toLowerCase();
  var rows = document.getElementById(tableId).getElementsByTagName('tr');
  for (var i = 1; i < rows.length; i++) {
    rows[i].style.display = rows[i].innerText.toLowerCase().indexOf(filter) > -1 ? '' : 'none';
  }
}
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => alert('Copied: ' + text.substring(0, 50) + '...'));
}
"""

# ─── Database ────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS targets (
        id INTEGER PRIMARY KEY AUTOINCREMENT, target TEXT NOT NULL,
        scan_date TEXT, scan_type TEXT, modules TEXT, duration_seconds REAL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS findings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, target_id INTEGER,
        module TEXT, finding_type TEXT, data TEXT, severity TEXT DEFAULT 'info',
        FOREIGN KEY(target_id) REFERENCES targets(id))""")
    conn.commit()
    conn.close()

def db_insert_target(target, scan_type, modules, duration):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO targets (target, scan_date, scan_type, modules, duration_seconds) VALUES (?,?,?,?,?)",
              (target, datetime.now().isoformat(), scan_type, json.dumps(modules), duration))
    tid = c.lastrowid
    conn.commit()
    conn.close()
    return tid

def db_insert_finding(target_id, module, finding_type, data, severity='info'):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    serialized = json.dumps(data) if isinstance(data, (dict, list)) else str(data)
    c.execute("INSERT INTO findings (target_id, module, finding_type, data, severity) VALUES (?,?,?,?,?)",
              (target_id, module, finding_type, serialized, severity))
    conn.commit()
    conn.close()

init_db()

# ─── Helpers ─────────────────────────────────────────────────────────────────
def ts():
    return datetime.now().strftime("[%H:%M:%S]")

def update_progress(task, done, total=20):
    progress["current"] = task
    progress["done"] = done
    pct = int((done / total * 100)) if total > 0 else 0
    bars = int(pct / 5)
    bar = "█" * bars + "░" * (20 - bars)
    with lock:
        print(Fore.CYAN + f"\r{ts()} [{bar}] {pct}% - {task} ({done}/{total})" + " " * 20)

def fetch_content(url, proxy=None, timeout=8, headers=None, max_size=5*1024*1024):
    try:
        h = {"User-Agent": USER_AGENT}
        if headers:
            h.update(headers)
        proxies = {"http": proxy, "https": proxy} if proxy else None
        r = requests.get(url, headers=h, proxies=proxies, timeout=timeout)
        r.raise_for_status()
        content = r.content
        if len(content) > max_size:
            content = content[:max_size]
        if url.lower().endswith(".gz") or (len(content) >= 2 and content[:2] == b"\x1f\x8b"):
            try:
                content = gzip.decompress(content)
            except Exception:
                pass
        enc = r.encoding or "utf-8"
        return content.decode(enc, errors="replace")
    except Exception:
        return None

def check_head(url, proxy=None, timeout=6):
    try:
        proxies = {"http": proxy, "https": proxy} if proxy else None
        r = requests.head(url, headers={"User-Agent": USER_AGENT}, proxies=proxies, timeout=timeout, allow_redirects=True)
        return r.status_code, r.headers.get("Content-Type", ""), dict(r.headers)
    except Exception:
        return None, "", {}

def run_command(cmd, timeout=120):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), -1

def extract_domain(url):
    p = urlparse(url)
    return p.netloc or p.path.split("/")[0]

def is_valid_domain(d):
    try:
        return "." in d and not d.startswith(".") and len(d) < 253
    except Exception:
        return False

# ─── Module 1: Subdomain Enumeration ─────────────────────────────────────────
def module_subdomain_enum(target, proxy=None):
    update_progress("Subdomain Enumeration", 1)
    domain = extract_domain(target).lstrip("www.")
    subdomains = set()

    with lock:
        print(Fore.CYAN + f"{ts()} [*] Running subfinder on {domain}...")
    stdout, _, _ = run_command(f"subfinder -d {domain} -silent 2>/dev/null")
    for line in stdout.strip().split("\n"):
        d = line.strip()
        if is_valid_domain(d):
            subdomains.add(d)

    with lock:
        print(Fore.CYAN + f"{ts()} [*] Running amass (passive) on {domain}...")
    stdout, _, _ = run_command(f"amass enum -passive -d {domain} 2>/dev/null")
    for line in stdout.strip().split("\n"):
        d = line.strip()
        if is_valid_domain(d):
            subdomains.add(d)

    # crt.sh fallback via requests
    try:
        r = requests.get(f"https://crt.sh/?q=%.{domain}&output=json", timeout=30)
        if r.status_code == 200:
            data = r.json()
            for entry in data:
                name = entry.get("name_value", "")
                for n in name.split("\n"):
                    n = n.strip().lower()
                    if is_valid_domain(n) and "*" not in n:
                        subdomains.add(n)
    except Exception:
        pass

    result = sorted(list(subdomains))
    update_progress("Subdomain Enumeration", 2)
    with lock:
        print(Fore.GREEN + f"{ts()} [+] Found {len(result)} subdomains")
    return result

# ─── Module 2: DNS Reconnaissance ────────────────────────────────────────────
def module_dns_recon(target, subdomains=None):
    update_progress("DNS Reconnaissance", 3)
    domain = extract_domain(target).lstrip("www.")
    dns_servers = ["8.8.8.8", "1.1.1.1", "9.9.9.9"]
    results = {"a": [], "aaaa": [], "mx": [], "ns": [], "txt": [], "spf": [], "dmarc": [], "zone_transfer": None, "subdomain_dns": {}}

    for rtype in ["A", "AAAA", "MX", "NS", "TXT"]:
        server = random.choice(dns_servers)
        stdout, _, _ = run_command(f"dig +short {rtype} @{server} {domain}")
        if stdout:
            records = [r.strip() for r in stdout.strip().split("\n") if r.strip()]
            key = rtype.lower()
            results[key] = records
            if rtype == "TXT":
                for r in records:
                    if "v=spf1" in r:
                        results["spf"] = r
                    if "v=DMARC1" in r:
                        results["dmarc"] = r

    # Zone transfer attempt
    for ns in results.get("ns", []):
        stdout, _, _ = run_command(f"dig axfr @{ns.strip('.')} {domain} 2>&1 | head -50")
        if stdout and "failed" not in stdout.lower() and "refused" not in stdout.lower() and len(stdout) > 100:
            results["zone_transfer"] = {"nameserver": ns, "records": stdout[:5000]}
            with lock:
                print(Fore.RED + f"{ts()} [!] ZONE TRANSFER SUCCESSFUL via {ns}!")
            break

    # Resolve subdomains
    if subdomains:
        for sd in subdomains[:50]:
            stdout, _, _ = run_command(f"dig +short A @8.8.8.8 {sd}")
            if stdout:
                results["subdomain_dns"][sd] = [r.strip() for r in stdout.strip().split("\n") if r.strip()]

    update_progress("DNS Reconnaissance", 4)
    return results

# ─── Module 3: Port Scanning ─────────────────────────────────────────────────
def module_port_scan(target, subdomains=None):
    update_progress("Port Scanning", 5)
    scan_targets = list(subdomains[:10]) if subdomains else [extract_domain(target).lstrip("www.")]
    results = {}

    for tgt in scan_targets:
        with lock:
            print(Fore.CYAN + f"{ts()} [*] Scanning {tgt} with nmap...")
        stdout, _, _ = run_command(f"nmap -T4 --top-ports 100 -sV --open -oG - {tgt} 2>/dev/null")
        if stdout:
            results[tgt] = parse_nmap_output(stdout)

    update_progress("Port Scanning", 6)
    return results

def parse_nmap_output(output):
    ports = []
    for line in output.split("\n"):
        if "/tcp" in line and "open" in line:
            parts = line.split()
            if len(parts) >= 3:
                port_info = parts[0].split("/")[0]
                service = parts[2] if len(parts) > 2 else "unknown"
                ports.append({"port": port_info, "protocol": "tcp", "service": service, "state": "open"})
    return ports

# ─── Module 4: Technology Fingerprinting ─────────────────────────────────────
def module_tech_fingerprint(target, subdomains=None):
    update_progress("Technology Fingerprinting", 7)
    results = {}
    scan_targets = [target.rstrip("/")] + ([s for s in (subdomains or [])[:3]])

    for tgt in scan_targets:
        tech_info = {}

        # Whatweb
        stdout, _, _ = run_command(f"whatweb --color=never -q {tgt} 2>/dev/null")
        if stdout:
            tech_info["whatweb"] = stdout.strip()

        # WAF detection
        stdout, _, _ = run_command(f"wafw00f -a {tgt} 2>/dev/null | head -5")
        if stdout and "No WAF" not in stdout:
            tech_info["waf"] = stdout.strip()

        # Headers + CMS detection
        try:
            r = requests.head(tgt, headers={"User-Agent": USER_AGENT}, timeout=10, allow_redirects=True)
            tech_info["headers"] = dict(r.headers)
            tech_info["server"] = r.headers.get("Server", "Unknown")
            tech_info["powered_by"] = r.headers.get("X-Powered-By", "")
            tech_info["cms"] = ""
            body = fetch_content(tgt, timeout=10)
            if body:
                body_lower = body.lower()
                if "wp-content" in body_lower or "wp-includes" in body_lower:
                    tech_info["cms"] = "WordPress"
                elif "joomla" in body_lower:
                    tech_info["cms"] = "Joomla"
                elif "drupal" in body_lower:
                    tech_info["cms"] = "Drupal"
                elif "laravel" in body_lower:
                    tech_info["cms"] = "Laravel"
                elif "django" in body_lower:
                    tech_info["cms"] = "Django"
                elif "express" in body_lower or "node.js" in body_lower:
                    tech_info["cms"] = "Node.js/Express"
                tech_info["frameworks"] = []
                for fw in ["jquery", "react", "vue", "angular", "bootstrap", "tailwind"]:
                    if fw in body_lower:
                        tech_info["frameworks"].append(fw.capitalize())
                tech_info["frameworks"] = tech_info["frameworks"] or ["None detected"]
        except Exception:
            pass

        if tech_info:
            results[tgt] = tech_info

    update_progress("Technology Fingerprinting", 8)
    return results

# ─── Module 5: Directory Brute-Forcing ───────────────────────────────────────
def module_dir_bruteforce(target, proxy=None, threads=10, wordlist=None, status_codes=None):
    update_progress("Directory Brute-Forcing", 9)
    base = target.rstrip("/") + "/"
    wl = wordlist or SMALL_WORDLIST
    status_filter = status_codes or [200, 204, 301, 302, 307, 403]
    results = []

    def worker(path):
        url = urljoin(base, path)
        status, ctype, headers = check_head(url, proxy)
        if status in status_filter:
            return {"url": url, "status": status, "content_type": ctype, "size": int(headers.get("Content-Length", 0))}
        return None

    with ThreadPoolExecutor(max_workers=threads) as ex:
        futures = {ex.submit(worker, w): w for w in wl}
        for fut in as_completed(futures):
            try:
                r = fut.result()
                if r:
                    results.append(r)
            except Exception:
                pass

    results.sort(key=lambda x: x["status"])
    update_progress("Directory Brute-Forcing", 10)
    with lock:
        print(Fore.GREEN + f"{ts()} [+] Found {len(results)} interesting paths")
    return results

# ─── Module 6: Vulnerability Scanning ────────────────────────────────────────
def module_nuclei_scan(target, subdomains=None):
    update_progress("Vulnerability Scanning", 11)
    domains = [target.rstrip("/")] + (subdomains or [])[:10]
    results = {"vulnerabilities": [], "info": []}

    for domain in domains:
        with lock:
            print(Fore.CYAN + f"{ts()} [*] Running nuclei on {domain}...")
        stdout, _, _ = run_command(f"nuclei -u {domain} -silent -json 2>/dev/null")
        if stdout:
            for line in stdout.strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line.strip())
                    severity = entry.get("info", {}).get("severity", "info")
                    if severity in ["high", "critical"]:
                        results["vulnerabilities"].append(entry)
                    else:
                        results["info"].append(entry)
                except Exception:
                    pass

    update_progress("Vulnerability Scanning", 12)
    return results

# ─── Module 7: JavaScript Analysis ───────────────────────────────────────────
def module_js_analysis(target):
    update_progress("JavaScript Analysis", 11)
    results = {"endpoints": set(), "secrets": [], "js_files": []}
    base_url = target.rstrip("/")

    try:
        r = requests.get(base_url, headers={"User-Agent": USER_AGENT}, timeout=10)
        if r.status_code == 200:
            js_files = re.findall(r'<script[^>]+src=["\']([^"\']+\.js[^"\']*)["\']', r.text)
            for js_file in js_files[:20]:
                js_url = urljoin(base_url, js_file)
                if js_url not in results["js_files"]:
                    results["js_files"].append(js_url)
                    js_content = fetch_content(js_url, timeout=10)
                    if js_content:
                        for pattern in JS_ENDPOINT_PATTERNS:
                            for match in re.finditer(pattern, js_content):
                                endpoint = match.group(1) if match.lastindex else match.group(0)
                                if endpoint and len(endpoint) < 200:
                                    results["endpoints"].add(endpoint)
                        for pattern, secret_type in JS_SECRET_PATTERNS:
                            for match in re.finditer(pattern, js_content, re.IGNORECASE):
                                secret = match.group(1) if match.lastindex else match.group(0)
                                if secret and len(secret) > 10:
                                    existing = [s["value"] for s in results["secrets"]]
                                    if secret not in existing:
                                        results["secrets"].append({"type": secret_type, "value": secret[:80] + "..." if len(secret) > 80 else secret, "file": js_url, "severity": "high"})
    except Exception as e:
        with lock:
            print(Fore.YELLOW + f"{ts()} [!] JS analysis error: {e}")

    results["endpoints"] = sorted(list(results["endpoints"]))
    update_progress("JavaScript Analysis", 12)
    return results

# ─── Module 8: Screenshot Capture ────────────────────────────────────────────
def module_screenshots(target, subdomains=None):
    update_progress("Screenshot Capture", 9)
    results = {"screenshots": []}
    targets_to_capture = [target.rstrip("/")] + ([s for s in (subdomains or [])[:5]])

    for tgt in targets_to_capture:
        try:
            opts = ChromiumOptions()
            opts.headless(True)
            opts.set_argument('--no-sandbox')
            opts.set_argument('--disable-dev-shm-usage')
            opts.set_argument('--disable-gpu')
            page = ChromiumPage(opts)
            page.get(tgt)
            page.wait.load_start()
            domain_safe = extract_domain(tgt).replace(":", "_").replace("/", "_")
            screenshot_path = os.path.join(BASE_OUTPUT, f"screenshot_{domain_safe}_{int(time.time())}.png")
            page.get_screenshot(screenshot_path)
            page.quit()
            results["screenshots"].append({"url": tgt, "path": screenshot_path, "timestamp": datetime.now().isoformat()})
            with lock:
                print(Fore.GREEN + f"{ts()} [+] Screenshot saved: {screenshot_path}")
        except Exception as e:
            with lock:
                print(Fore.YELLOW + f"{ts()} [!] Screenshot failed for {tgt}: {e}")
        time.sleep(1)

    update_progress("Screenshot Capture", 10)
    return results

# ─── Module 9: Wayback Machine Mining ────────────────────────────────────────
def module_wayback(target):
    update_progress("Wayback Machine Mining", 12)
    domain = extract_domain(target).lstrip("www.")
    urls = set()
    try:
        api_url = f"http://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=json&fl=original&collapse=urlkey"
        r = requests.get(api_url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and len(data) > 1:
                urls = set(row[0] for row in data[1:] if len(row) > 0)
    except Exception:
        pass
    results = sorted(list(urls))[:500]
    update_progress("Wayback Machine Mining", 13)
    return results

# ─── Module 10: SSL/TLS Analysis ─────────────────────────────────────────────
def module_ssl_analysis(target):
    update_progress("SSL/TLS Analysis", 13)
    domain = extract_domain(target).lstrip("www.")
    results = {"certificates": [], "issues": []}

    # openssl cert extraction
    stdout, _, _ = run_command(f"echo | openssl s_client -connect {domain}:443 -servername {domain} 2>/dev/null | openssl x509 -noout -text 2>/dev/null")
    if stdout:
        cert = {}
        cert["raw"] = stdout[:5000]

        expiry_match = re.search(r"Not After\s*:\s*(.+)", stdout)
        if expiry_match:
            try:
                expiry_str = expiry_match.group(1).strip()
                expiry_date = datetime.strptime(expiry_str, "%b %d %H:%M:%S %Y %Z")
                days_left = (expiry_date - datetime.now()).days
                cert["expiry"] = expiry_str
                cert["days_until_expiry"] = days_left
                if days_left < 30:
                    results["issues"].append({"type": "cert_expiry_warning", "message": f"Certificate expires in {days_left} days!", "severity": "high"})
                if days_left < 0:
                    results["issues"].append({"type": "cert_expired", "message": "Certificate is EXPIRED!", "severity": "critical"})
            except Exception:
                pass

        subject_match = re.search(r"Subject:.*CN\s*=\s*(.+)", stdout)
        if subject_match:
            cert["subject_cn"] = subject_match.group(1).strip()

        san_matches = re.findall(r"DNS:(\S+)", stdout)
        if san_matches:
            cert["san"] = list(set(san_matches))

        results["certificates"].append(cert)

    # testssl.sh for cipher analysis
    stdout, _, _ = run_command(f"testssl --protocol {domain} 2>/dev/null | grep -E '(SSL|TLS)' | head -10")
    if stdout:
        results["protocols"] = stdout.strip()

    update_progress("SSL/TLS Analysis", 14)
    return results

# ─── Module 11: Subdomain Takeover Detection ─────────────────────────────────
def module_subdomain_takeover(subdomains):
    update_progress("Subdomain Takeover Detection", 13)
    results = {"vulnerable": [], "checked": 0}

    for sd in (subdomains or [])[:50]:
        results["checked"] += 1
        stdout, _, _ = run_command(f"dig +short CNAME {sd}")
        if not stdout:
            continue
        cname = stdout.strip().lower()

        for fp in SUBDOMAIN_TAKEOVER_FINGERPRINTS:
            if any(c in cname for c in fp["cnames"]):
                try:
                    r = requests.get(f"https://{sd}", headers={"User-Agent": USER_AGENT}, timeout=10, allow_redirects=True)
                    body = r.text.lower()
                    if any(f.lower() in body for f in fp["fingerprint"]):
                        results["vulnerable"].append({
                            "subdomain": sd, "cname": cname,
                            "service": fp["service"], "status_code": r.status_code
                        })
                        with lock:
                            print(Fore.RED + f"{ts()} [!] POSSIBLE TAKEOVER: {sd} ({fp['service']})")
                except Exception:
                    pass

    update_progress("Subdomain Takeover Detection", 14)
    return results

# ─── Module 12: Email Harvesting ─────────────────────────────────────────────
def module_email_harvest(target):
    update_progress("Email Harvesting", 14)
    emails = set()
    try:
        body = fetch_content(target, timeout=10)
        if body:
            found = re.findall(EMAIL_PATTERN, body)
            emails.update(found)
        # Also check /contact, /about, /team pages
        for page in ["/contact", "/about", "/team", "/info", "/support"]:
            page_url = urljoin(target, page)
            body = fetch_content(page_url, timeout=10)
            if body:
                found = re.findall(EMAIL_PATTERN, body)
                emails.update(found)
    except Exception:
        pass
    results = sorted(list(emails))
    update_progress("Email Harvesting", 15)
    with lock:
        print(Fore.GREEN + f"{ts()} [+] Found {len(results)} email addresses")
    return results

# ─── Module 13: Cloud Bucket Detection ────────────────────────────────────────
def module_cloud_buckets(target):
    update_progress("Cloud Bucket Detection", 15)
    results = {"buckets": [], "misconfigured": []}
    domain = extract_domain(target).lstrip("www.")
    base_domain = domain.split(".")[0]

    # Check common bucket naming patterns
    bucket_names = [
        base_domain, domain, f"{base_domain}-assets", f"{base_domain}-static",
        f"{base_domain}-media", f"{base_domain}-uploads", f"{base_domain}-backup",
        f"www.{base_domain}", f"cdn.{base_domain}", f"assets.{base_domain}"
    ]

    for bucket_name in bucket_names[:15]:
        # AWS S3
        s3_url = f"https://{bucket_name}.s3.amazonaws.com/"
        try:
            r = requests.head(s3_url, timeout=5)
            if r.status_code == 200:
                results["buckets"].append({"type": "AWS S3", "url": s3_url, "status": "accessible", "severity": "high"})
            elif r.status_code == 403:
                results["buckets"].append({"type": "AWS S3", "url": s3_url, "status": "exists_but_private", "severity": "info"})
        except Exception:
            pass

        # Azure Blob
        azure_url = f"https://{bucket_name}.blob.core.windows.net/"
        try:
            r = requests.head(azure_url, timeout=5)
            if r.status_code == 200:
                results["buckets"].append({"type": "Azure Blob", "url": azure_url, "status": "accessible", "severity": "high"})
        except Exception:
            pass

        # Google Cloud Storage
        gcs_url = f"https://storage.googleapis.com/{bucket_name}"
        try:
            r = requests.head(gcs_url, timeout=5)
            if r.status_code == 200:
                results["buckets"].append({"type": "GCS", "url": gcs_url, "status": "accessible", "severity": "high"})
        except Exception:
            pass

    # Scan HTML/JS for cloud storage references
    try:
        body = fetch_content(target, timeout=10)
        if body:
            for pattern, provider in CLOUD_BUCKET_PATTERNS:
                matches = re.findall(pattern, body, re.IGNORECASE)
                for match in matches[:5]:
                    results["buckets"].append({"type": provider, "found_in": "html/js", "reference": match})
    except Exception:
        pass

    update_progress("Cloud Bucket Detection", 16)
    return results

# ─── Module 14: GraphQL Detection ────────────────────────────────────────────
def module_graphql_detection(target):
    update_progress("GraphQL Detection", 16)
    results = {"endpoints": [], "introspection_enabled": False}
    base = target.rstrip("/")

    graphql_paths = ["/graphql", "/graphiql", "/api/graphql", "/v1/graphql", "/v2/graphql", "/query"]

    for path in graphql_paths:
        url = base + path
        try:
            # Check if endpoint exists
            r = requests.post(url, json={"query": "{__schema{types{name}}}"}, headers={"Content-Type": "application/json"}, timeout=10)
            if r.status_code == 200:
                data = r.json()
                results["endpoints"].append({"url": url, "status": r.status_code})
                if "data" in data and "__schema" in data.get("data", {}):
                    results["introspection_enabled"] = True
                    results["introspection_endpoint"] = url
                    with lock:
                        print(Fore.RED + f"{ts()} [!] GRAPHQL INTROSPECTION ENABLED: {url}")
                break
            # Also check GET
            r2 = requests.get(url, timeout=10)
            if r2.status_code == 200 and "graphiql" in r2.text.lower():
                results["endpoints"].append({"url": url, "status": r2.status_code, "note": "GraphiQL interface detected"})
        except Exception:
            pass

    update_progress("GraphQL Detection", 17)
    return results

# ─── Module 15: Git Exposure ─────────────────────────────────────────────────
def module_git_exposure(target):
    update_progress("Git Exposure Check", 17)
    results = {"exposed": False, "files_found": [], "details": ""}
    base = target.rstrip("/")

    git_paths = ["/.git/", "/.git/HEAD", "/.git/config", "/.git/refs/heads/master",
                 "/.git/objects/", "/.git/index", "/.git/description", "/.git/FETCH_HEAD",
                 "/.gitignore", "/.gitlab-ci.yml"]

    for path in git_paths:
        url = base + path
        try:
            r = requests.head(url, timeout=5)
            if r.status_code == 200 or r.status_code == 403:
                # 403 on .git/ is still suspicious
                body_resp = requests.get(url, timeout=5)
                if body_resp.status_code == 200:
                    results["files_found"].append({"path": path, "status": 200, "size": len(body_resp.text)})
                    if "ref:" in body_resp.text or "PACK" in body_resp.text[:20]:
                        results["exposed"] = True
                        with lock:
                            print(Fore.RED + f"{ts()} [!] EXPOSED GIT REPO: {url}")
        except Exception:
            pass

    update_progress("Git Exposure Check", 18)
    return results

# ─── Module 16: Parameter Discovery ──────────────────────────────────────────
def module_param_discovery(target):
    update_progress("Parameter Discovery", 18)
    results = {"parameters": [], "endpoints_with_params": []}
    base = target.rstrip("/")

    try:
        body = fetch_content(base, timeout=10)
        if body:
            # Find form parameters
            form_inputs = re.findall(r'<input[^>]+name=["\']([^"\']+)["\']', body, re.IGNORECASE)
            results["parameters"].extend(form_inputs)

            # Find URL parameters in links
            links = re.findall(r'href=["\']([^"\']*\?[^"\']+)["\']', body)
            for link in links[:30]:
                parsed = urlparse(link)
                params = parse_qs(parsed.query)
                if params:
                    results["endpoints_with_params"].append({"url": link, "params": list(params.keys())})

            # Find API parameters in JS
            api_params = re.findall(r'[?&](\w+)=', body)
            unique_params = list(set(api_params))
            results["api_parameters"] = [p for p in unique_params if len(p) < 50][:50]
    except Exception:
        pass

    results["parameters"] = list(set(results["parameters"]))
    update_progress("Parameter Discovery", 19)
    return results

# ─── Module 17: Rate Limiting Detection ──────────────────────────────────────
def module_rate_limit_detection(target):
    update_progress("Rate Limiting Detection", 19)
    results = {"rate_limited": False, "tests_performed": 0, "responses": []}
    base = target.rstrip("/") + "/"

    # Send 10 rapid requests
    for i in range(10):
        try:
            r = requests.get(base + f"test{random.randint(1000,9999)}", headers={"User-Agent": USER_AGENT}, timeout=5)
            results["tests_performed"] += 1
            results["responses"].append({"iteration": i, "status": r.status_code, "headers": dict(r.headers)})
            if r.status_code == 429:
                results["rate_limited"] = True
                with lock:
                    print(Fore.GREEN + f"{ts()} [+] Rate limiting detected (429 response)")
                break
            time.sleep(0.1)
        except Exception:
            pass

    update_progress("Rate Limiting Detection", 20)
    return results

# ─── Module 18: API Key Scanning ─────────────────────────────────────────────
def module_api_key_scan(target):
    update_progress("API Key Scanning", 18)
    results = {"keys_found": []}
    try:
        body = fetch_content(target, timeout=10)
        if not body:
            update_progress("API Key Scanning", 19)
            return results

        # Scan for common API keys
        patterns = [
            (r'(?:AKIA[0-9A-Z]{16})', "AWS Access Key ID"),
            (r'(?:AIza[0-9A-Za-z\-_]{35})', "Google API Key"),
            (r'(?:sk[_-][a-zA-Z0-9]{20,})', "Secret Key"),
            (r'(?:pk[_-][a-zA-Z0-9]{20,})', "Public Key"),
            (r'(?:gh[pousr]_[a-zA-Z0-9_]{20,})', "GitHub Token"),
            (r'(?:glpat-[a-zA-Z0-9\-_]{20,})', "GitLab Token"),
            (r'(?:xox[baprs]-[a-zA-Z0-9\-]{10,})', "Slack Token"),
            (r'(?:ey[a-zA-Z0-9]{20,}\.[a-zA-Z0-9]{20,}\.[a-zA-Z0-9]{20,})', "JWT Token"),
        ]

        for pattern, key_type in patterns:
            matches = re.findall(pattern, body)
            for match in matches[:5]:
                results["keys_found"].append({"type": key_type, "value": match[:30] + "...", "severity": "critical"})

        # Scan response headers
        try:
            r = requests.get(target, headers={"User-Agent": USER_AGENT}, timeout=10)
            for header, value in r.headers.items():
                for pattern, key_type in patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        results["keys_found"].append({"type": key_type, "location": f"header: {header}", "value": value[:30] + "..."})
        except Exception:
            pass

    except Exception:
        pass

    update_progress("API Key Scanning", 19)
    if results["keys_found"]:
        with lock:
            print(Fore.RED + f"{ts()} [!] Found {len(results['keys_found'])} potential API keys/secrets!")
    return results

# ─── Module 19: Whois & Registration ─────────────────────────────────────────
def module_whois(target):
    update_progress("Whois Lookup", 19)
    domain = extract_domain(target).lstrip("www.")
    results = {"whois": "", "registrar": "", "creation_date": "", "expiry_date": "", "nameservers": []}

    stdout, _, _ = run_command(f"whois {domain} 2>/dev/null")
    if stdout:
        results["whois"] = stdout[:5000]
        registrar = re.search(r"Registrar:\s*(.+)", stdout)
        if registrar:
            results["registrar"] = registrar.group(1).strip()
        creation = re.search(r"Creation Date:\s*(.+)", stdout)
        if creation:
            results["creation_date"] = creation.group(1).strip()
        expiry = re.search(r"Registry Expiry Date:\s*(.+)", stdout)
        if expiry:
            results["expiry_date"] = expiry.group(1).strip()
        ns_entries = re.findall(r"Name Server:\s*(.+)", stdout)
        results["nameservers"] = [ns.strip().upper() for ns in ns_entries]

    update_progress("Whois Lookup", 20)
    return results

# ─── Module 20: Robots.txt + Sitemap ─────────────────────────────────────────
def module_sitemap_robots(target, proxy=None, quick_mode=False):
    update_progress("Robots.txt + Sitemap", 8)
    if not target.endswith("/"):
        target += "/"
    result = {"robots": None, "disallow": [], "allow": [], "sitemaps": [], "comments": [], "discovered_sitemaps": [], "sitemap_urls": []}

    timeout = 4 if quick_mode else 8
    locations = COMMON_SITEMAP_LOCATIONS[:3] if quick_mode else COMMON_SITEMAP_LOCATIONS

    content = fetch_content(target + "robots.txt", proxy, timeout=timeout)
    if content:
        result["robots"] = content
        result["disallow"] = re.findall(r"(?im)^\s*Disallow\s*:\s*(.*)$", content)
        result["allow"] = re.findall(r"(?im)^\s*Allow\s*:\s*(.*)$", content)
        result["sitemaps"] = re.findall(r"(?im)^\s*Sitemap\s*:\s*(.*)$", content)
        result["comments"] = re.findall(r"(?m)#\s*(.*)$", content)

    if not result["sitemaps"]:
        for loc in locations:
            txt = fetch_content(target.rstrip("/") + loc, proxy, timeout=timeout)
            if txt:
                result["discovered_sitemaps"].append(target.rstrip("/") + loc)

    sitemaps_to_crawl = list(dict.fromkeys(result.get("sitemaps", []) + result.get("discovered_sitemaps", [])))
    if sitemaps_to_crawl:
        all_urls = []
        for sm in sitemaps_to_crawl:
            txt = fetch_content(sm, proxy, timeout=timeout)
            if txt:
                try:
                    root = etree.fromstring(txt.encode("utf-8"))
                    for loc in root.findall(".//{*}loc"):
                        if loc is not None and loc.text:
                            all_urls.append(loc.text.strip())
                except Exception:
                    for line in txt.splitlines():
                        line = line.strip()
                        if line.startswith("http"):
                            all_urls.append(line)
        result["sitemap_urls"] = list(dict.fromkeys(all_urls))

    update_progress("Robots.txt + Sitemap", 9)
    return result

# ─── HTML Report Generation ──────────────────────────────────────────────────
def generate_html_report(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    out = os.path.splitext(json_path)[0] + ".html"
    domain = data.get("target", "unknown")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    modules_run = data.get("modules_run", [])
    duration = data.get("scan_duration", 0)

    # Stub-safe data extraction
    def safe_list(data, key, default=None):
        val = data.get(key, default or [])
        return val if isinstance(val, list) else []
    def safe_dict_get(data, key, subkey, default=None):
        val = data.get(key, {})
        if isinstance(val, dict):
            return val.get(subkey, default)
        return default

    subdomains = safe_list(data, "subdomains")
    ports = data.get("ports", {})
    total_ports = sum(len(v) for v in ports.values()) if isinstance(ports, dict) and ports else 0
    vuln_count = len(safe_dict_get(data, "vulnerabilities", "vulnerabilities", []))
    paths = safe_dict_get(data, "hidden_paths", "positives", [])
    secrets = safe_dict_get(data, "js_analysis", "secrets", [])
    emails = safe_list(data, "emails")
    cloud_buckets = safe_dict_get(data, "cloud_buckets", "buckets", [])
    api_keys = safe_dict_get(data, "api_keys", "keys_found", [])
    takeover = safe_dict_get(data, "subdomain_takeover", "vulnerable", [])
    git_exposed = safe_dict_get(data, "git_exposure", "exposed", False)
    graphql = safe_dict_get(data, "graphql", "introspection_enabled", False)

    parts = [f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>RoboRecon v8.0 — {html_module.escape(domain)}</title>
<style>{TEMPLATE_CSS}</style></head><body><div class="container">
<h1>🤖 RoboRecon v8.0 ULTIMATE</h1>
<div class="meta">Target: {html_module.escape(domain)} | Scanned: {now} | Duration: {duration:.1f}s | Modules: {len(modules_run)}</div>"""]

    # Critical alerts
    critical_findings = []
    if vuln_count > 0:
        critical_findings.append(("critical", f"{vuln_count} high/critical vulnerabilities found"))
    if secrets:
        critical_findings.append(("critical", f"{len(secrets)} secrets exposed in JS files"))
    if api_keys:
        critical_findings.append(("critical", f"{len(api_keys)} API keys/tokens detected"))
    if takeover:
        critical_findings.append(("critical", f"{len(takeover)} subdomain takeover vulnerabilities"))
    if git_exposed:
        critical_findings.append(("critical", "Git repository exposed!"))
    if graphql:
        critical_findings.append(("high", "GraphQL introspection enabled"))
    if cloud_buckets:
        accessible = [b for b in cloud_buckets if b.get("status") == "accessible"]
        if accessible:
            critical_findings.append(("high", f"{len(accessible)} accessible cloud storage buckets"))

    if critical_findings:
        parts.append('<div class="section">')
        for severity, msg in critical_findings:
            parts.append(f'<div class="alert alert-{severity}">⚠️ {html_module.escape(msg)}</div>')
        parts.append('</div>')

    # Summary cards
    parts.append('<div class="summary">')
    for label, value in [
        ("Subdomains", len(subdomains)), ("Open Ports", total_ports),
        ("Vulnerabilities", vuln_count), ("Hidden Paths", len(paths)),
        ("Emails", len(emails)), ("Cloud Buckets", len(cloud_buckets)),
        ("API Keys", len(api_keys)), ("JS Secrets", len(secrets))
    ]:
        parts.append(f'<div class="card"><div class="number">{value}</div><div class="label">{label}</div></div>')
    parts.append('</div>')

    # Sections
    if subdomains:
        parts.append(f'<div class="section"><h2>🌐 Subdomains ({len(subdomains)})</h2>')
        parts.append(f'<input type="text" class="filter-input" id="filter-sd" placeholder="Filter subdomains..." onkeyup="filterTable(\'filter-sd\',\'table-sd\')">')
        parts.append('<table id="table-sd"><thead><tr><th onclick="sortTable(0,\'table-sd\')">Subdomain</th><th>IP(s)</th></tr></thead><tbody>')
        dns_data = data.get("dns", {}).get("subdomain_dns", {}) if isinstance(data.get("dns"), dict) else {}
        for s in subdomains[:100]:
            ips = ", ".join(dns_data.get(s, ["N/A"]))[:200]
            parts.append(f'<tr><td><a href="https://{html_module.escape(s)}" target="_blank">{html_module.escape(s)}</a></td><td>{html_module.escape(ips)}</td></tr>')
        parts.append('</tbody></table></div>')

    if ports and isinstance(ports, dict) and "note" not in ports:
        parts.append('<div class="section"><h2>🚪 Open Ports</h2>')
        for host, ports_list in ports.items():
            if not isinstance(ports_list, list):
                continue
            parts.append(f'<h3>{html_module.escape(host)}</h3>')
            parts.append('<table><thead><tr><th>Port</th><th>Protocol</th><th>Service</th></tr></thead><tbody>')
            for p in ports_list:
                if isinstance(p, dict):
                    parts.append(f'<tr><td>{p["port"]}</td><td>{p["protocol"]}</td><td>{p["service"]}</td></tr>')
            parts.append('</tbody></table>')
        parts.append('</div>')

    if emails:
        parts.append(f'<div class="section"><h2>📧 Email Addresses ({len(emails)})</h2>')
        parts.append('<table><tbody>')
        for e in emails:
            parts.append(f'<tr><td>{html_module.escape(e)}</td></tr>')
        parts.append('</tbody></table></div>')

    if secrets or api_keys:
        parts.append('<div class="section"><h2>🔑 Secrets & API Keys</h2>')
        all_secrets = [s for s in (secrets + api_keys) if isinstance(s, dict)]
        for s in all_secrets:
            sev = s.get("severity", "high")
            parts.append(f'<div class="alert alert-{"critical" if sev == "critical" else "high"}">')
            parts.append(f'<strong>{html_module.escape(s.get("type", "Unknown"))}</strong><br>')
            parts.append(f'<code>{html_module.escape(s.get("value", ""))}</code>')
            if "file" in s:
                parts.append(f'<br><small>Source: {html_module.escape(s["file"])}</small>')
            parts.append('</div>')
        parts.append('</div>')

    if cloud_buckets:
        parts.append(f'<div class="section"><h2>☁️ Cloud Storage Buckets ({len(cloud_buckets)})</h2>')
        parts.append('<table><thead><tr><th>Type</th><th>URL</th><th>Status</th></tr></thead><tbody>')
        for b in cloud_buckets[:50]:
            sev_class = "badge-red" if b.get("status") == "accessible" else "badge-gray"
            parts.append(f'<tr><td>{html_module.escape(b.get("type", ""))}</td><td><a href="{html_module.escape(b.get("url", ""))}" target="_blank">{html_module.escape(b.get("url", ""))}</a></td><td><span class="badge {sev_class}">{html_module.escape(str(b.get("status", "")))}</span></td></tr>')
        parts.append('</tbody></table></div>')

    if paths:
        parts.append(f'<div class="section"><h2>📁 Hidden Paths ({len(paths)})</h2>')
        parts.append(f'<input type="text" class="filter-input" id="filter-paths" placeholder="Filter paths..." onkeyup="filterTable(\'filter-paths\',\'table-paths\')">')
        parts.append('<table id="table-paths"><thead><tr><th>URL</th><th>Status</th><th>Content-Type</th></tr></thead><tbody>')
        for p in paths[:100]:
            parts.append(f'<tr><td><a href="{html_module.escape(p["url"])}" target="_blank">{html_module.escape(p["url"])}</a></td><td><span class="badge badge-green">{p["status"]}</span></td><td>{html_module.escape(str(p.get("content_type", "")))}</td></tr>')
        parts.append('</tbody></table></div>')

    if takeover:
        parts.append(f'<div class="section"><h2>⚠️ Subdomain Takeover ({len(takeover)})</h2>')
        for t in takeover:
            parts.append(f'<div class="alert alert-critical">')
            parts.append(f'<strong>{html_module.escape(t["subdomain"])}</strong> → {html_module.escape(t["service"])} (CNAME: {html_module.escape(t["cname"])})')
            parts.append('</div>')
        parts.append('</div>')

    if data.get("graphql", {}).get("introspection_enabled"):
        parts.append('<div class="section"><h2>🔮 GraphQL</h2>')
        gq = data["graphql"]
        parts.append(f'<div class="alert alert-high">Introspection enabled at: <code>{html_module.escape(gq.get("introspection_endpoint", ""))}</code></div>')
        parts.append('<pre>' + html_module.escape(json.dumps(gq, indent=2)) + '</pre></div>')

    if data.get("ssl_analysis") and isinstance(data["ssl_analysis"], dict) and "note" not in data["ssl_analysis"]:
        parts.append('<div class="section"><h2>🔒 SSL/TLS</h2><pre>' + html_module.escape(json.dumps(data["ssl_analysis"], indent=2)) + '</pre></div>')

    wayback_data = data.get("wayback")
    if wayback_data and isinstance(wayback_data, list):
        parts.append(f'<div class="section"><h2>🕰️ Wayback URLs ({len(wayback_data)})</h2>')
        parts.append('<table><tbody>')
        for u in wayback_data[:100]:
            if isinstance(u, str):
                parts.append(f'<tr><td><a href="{html_module.escape(u)}" target="_blank">{html_module.escape(u)}</a></td></tr>')
        parts.append('</tbody></table></div>')

    whois_data = data.get("whois", {})
    if isinstance(whois_data, dict) and whois_data.get("whois"):
        parts.append('<div class="section"><h2>📋 Whois</h2><pre>' + html_module.escape(whois_data.get("whois", "")[:3000]) + '</pre></div>')

    sm_data = data.get("sitemap_robots", {})
    if isinstance(sm_data, dict) and sm_data.get("robots"):
        parts.append('<div class="section"><h2>📋 Robots.txt</h2><pre>' + html_module.escape(sm_data["robots"][:3000]) + '</pre></div>')

    parts.append(f'</div><script>{TEMPLATE_JS}</script></body></html>')

    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    return out

# ─── Report Save ──────────────────────────────────────────────────────────────
def save_report(domain, data, export_csv=False, html_report=False, auto_open=False):
    tsf = datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_path = os.path.join(BASE_OUTPUT, domain, tsf)
    os.makedirs(dir_path, exist_ok=True)

    json_path = os.path.join(dir_path, "report.json")
    txt_path = os.path.join(dir_path, "report.txt")
    csv_path = os.path.join(dir_path, "urls.csv")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"=== RoboRecon v8.0 ULTIMATE Report: {domain} ===\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"Modules Run: {', '.join(data.get('modules_run', []))}\n")
        f.write(f"Duration: {data.get('scan_duration', 0):.1f}s\n\n")
        for k, v in data.items():
            if k in ["target", "modules_run", "scan_duration", "scan_start", "scan_end", "profile"]:
                continue
            f.write(f"[{k.upper()}]\n")
            if isinstance(v, list):
                for item in v[:100]:
                    if isinstance(item, str):
                        f.write(f"  - {item}\n")
                    elif isinstance(item, dict):
                        f.write(f"  {json.dumps(item, indent=4)}\n")
            elif isinstance(v, dict):
                f.write(json.dumps(v, indent=2, default=str) + "\n")
            f.write("\n")

    if export_csv:
        urls = []
        sr = data.get("sitemap_robots", {})
        if isinstance(sr, dict):
            urls.extend(sr.get("sitemap_urls", []))
        hp = data.get("hidden_paths", {})
        if isinstance(hp, dict):
            urls.extend([p.get("url", "") for p in hp.get("positives", [])])
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["url", "source"])
            for u in urls[:1000]:
                writer.writerow([u, "discovered"])

    with lock:
        print(Fore.GREEN + f"{ts()} [+] Reports saved: {dir_path}")

    if html_report:
        try:
            html_path = generate_html_report(json_path)
            with lock:
                print(Fore.GREEN + f"{ts()} [+] HTML report: {html_path}")
            if auto_open:
                webbrowser.open("file://" + os.path.abspath(html_path))
        except Exception as e:
            import traceback
            with lock:
                print(Fore.YELLOW + f"{ts()} [!] HTML generation failed: {e}")
                traceback.print_exc()

# ─── Main Recon Engine ───────────────────────────────────────────────────────
def full_recon(target, proxy=None, profile="standard", threads=10, export_csv=False, html_report=False, auto_open=False):
    start_time = time.time()
    domain_name = extract_domain(target).replace("/", "_").replace(":", "_")
    if not target.startswith("http"):
        target = "https://" + target

    with lock:
        print(Fore.CYAN + f"\n{ts()} ╔══════════════════════════════════════════════╗")
        print(Fore.CYAN + f"{ts()} ║  RoboRecon v8.0 ULTIMATE - Elite Hacker Suite ║")
        print(Fore.CYAN + f"{ts()} ╚══════════════════════════════════════════════╝\n")
        print(Fore.WHITE + f"{ts()} [*] Target: {target}")
        print(Fore.WHITE + f"{ts()} [*] Profile: {profile}")
        print(Fore.WHITE + f"{ts()} [*] Threads: {threads}\n")

    result = {"target": target, "scan_start": datetime.now().isoformat(), "profile": profile, "modules_run": []}

    # ── QUICK PROFILE: robots.txt + sitemap only ─────────────────────────
    if profile == "quick":
        sitemap = module_sitemap_robots(target, proxy, quick_mode=True)
        result["sitemap_robots"] = sitemap
        result["modules_run"].append("sitemap_robots")
        # Set stub values for everything else
        for key in ["subdomains", "dns", "subdomain_takeover", "tech_fingerprint",
                     "ports", "hidden_paths", "js_analysis", "emails", "wayback",
                     "cloud_buckets", "graphql", "git_exposure", "ssl_analysis",
                     "whois", "api_keys", "parameters", "rate_limiting",
                     "vulnerabilities", "screenshots"]:
            result[key] = {"note": "skipped in quick profile"}
    else:
        # ── STANDARD/DEEP/NUCLEAR ────────────────────────────────────────
        subdomains = []
        if profile in ["standard", "deep", "nuclear"]:
            subdomains = module_subdomain_enum(target, proxy)
            result["subdomains"] = subdomains
            result["modules_run"].append("subdomain_enum")

            dns = module_dns_recon(target, subdomains)
            result["dns"] = dns
            result["modules_run"].append("dns_recon")

            takeover = module_subdomain_takeover(subdomains) if profile in ["deep", "nuclear"] else {"note": "skipped"}
            result["subdomain_takeover"] = takeover
            result["modules_run"].append("subdomain_takeover" if profile in ["deep", "nuclear"] else "skipped")

        # Phase 2: Active Recon
        sitemap = module_sitemap_robots(target, proxy)
        result["sitemap_robots"] = sitemap
        result["modules_run"].append("sitemap_robots")

        if profile in ["standard", "deep", "nuclear"]:
            tech = module_tech_fingerprint(target, subdomains or None)
            result["tech_fingerprint"] = tech
            result["modules_run"].append("tech_fingerprint")

        if profile in ["deep", "nuclear"]:
            ports = module_port_scan(target, subdomains[:20] if subdomains else None)
            result["ports"] = ports
            result["modules_run"].append("port_scan")

        hidden_wl = LARGE_WORDLIST if profile == "nuclear" else (MEDIUM_WORDLIST if profile == "deep" else SMALL_WORDLIST)
        if profile in ["standard", "deep", "nuclear"]:
            hidden = module_dir_bruteforce(target, proxy, threads=threads, wordlist=hidden_wl)
            result["hidden_paths"] = {"all_results": hidden, "positives": hidden}
            result["modules_run"].append("hidden_paths")
        else:
            result["hidden_paths"] = {"note": "skipped in quick profile"}

        js = module_js_analysis(target)
        result["js_analysis"] = js
        result["modules_run"].append("js_analysis")

        emails = module_email_harvest(target)
        result["emails"] = emails
        result["modules_run"].append("email_harvest")

        if profile in ["standard", "deep", "nuclear"]:
            wayback = module_wayback(target)
            result["wayback"] = wayback
            result["modules_run"].append("wayback")

        cloud = module_cloud_buckets(target)
        result["cloud_buckets"] = cloud
        result["modules_run"].append("cloud_buckets")

        graphql = module_graphql_detection(target)
        result["graphql"] = graphql
        result["modules_run"].append("graphql_detection")

        git_exp = module_git_exposure(target)
        result["git_exposure"] = git_exp
        result["modules_run"].append("git_exposure")

        if profile in ["deep", "nuclear"]:
            ssl = module_ssl_analysis(target)
            result["ssl_analysis"] = ssl
            result["modules_run"].append("ssl_analysis")

            whois_data = module_whois(target)
            result["whois"] = whois_data
            result["modules_run"].append("whois")

        api_keys = module_api_key_scan(target)
        result["api_keys"] = api_keys
        result["modules_run"].append("api_key_scan")

        params = module_param_discovery(target)
        result["parameters"] = params
        result["modules_run"].append("param_discovery")

        rate_limit = module_rate_limit_detection(target)
        result["rate_limiting"] = rate_limit
        result["modules_run"].append("rate_limit_detection")

        if profile in ["deep", "nuclear"]:
            vulns = module_nuclei_scan(target, subdomains or None)
            result["vulnerabilities"] = vulns
            result["modules_run"].append("vulnerability_scan")

        if profile == "nuclear":
            shots = module_screenshots(target, subdomains or None)
            result["screenshots"] = shots
            result["modules_run"].append("screenshots")

    duration = time.time() - start_time
    result["scan_duration"] = round(duration, 2)
    result["scan_end"] = datetime.now().isoformat()

    db_insert_target(target, profile, result["modules_run"], duration)
    save_report(domain_name, result, export_csv, html_report, auto_open)

    with lock:
        print(Fore.GREEN + f"\n{ts()} [✓] Recon complete in {duration:.1f}s. {len(result['modules_run'])} modules executed.\n")

# ─── CLI ─────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(prog="RoboRecon v8.0 ULTIMATE", description="Elite Hacker Reconnaissance Framework")
    p.add_argument("-u", "--url", help="Target domain or URL")
    p.add_argument("targets", nargs="*", help="Targets or file containing list")
    p.add_argument("--proxy", help="Proxy/Tor e.g. socks5h://127.0.0.1:9050")
    p.add_argument("--profile", choices=["quick", "standard", "deep", "nuclear"], default="standard",
                   help="Recon profile")
    p.add_argument("--threads", type=int, default=10, help="Worker threads")
    p.add_argument("--export-csv", action="store_true", help="Export URLs to CSV")
    p.add_argument("--html-report", action="store_true", help="Generate HTML dashboard")
    p.add_argument("--open", action="store_true", help="Open report after generation")
    p.add_argument("--list-modules", action="store_true", help="List available modules")
    args = p.parse_args()

    if args.list_modules:
        print(Fore.CYAN + "\n┌─ Available Modules (20) ──────────────────────────┐")
        modules = [
            "1.  Subdomain Enumeration     11. Subdomain Takeover Detection",
            "2.  DNS Reconnaissance         12. Email Harvesting",
            "3.  Port Scanning              13. Cloud Bucket Detection",
            "4.  Tech Fingerprinting        14. GraphQL Detection",
            "5.  Dir Brute-Forcing          15. Git Exposure Check",
            "6.  Vulnerability Scan         16. Parameter Discovery",
            "7.  JavaScript Analysis        17. Rate Limiting Detection",
            "8.  Screenshot Capture         18. API Key Scanning",
            "9.  Wayback Mining             19. Whois Lookup",
            "10. SSL/TLS Analysis           20. Robots.txt + Sitemap",
        ]
        for m in modules:
            print(Fore.CYAN + f"│  {m}  │")
        print("└──────────────────────────────────────────────────┘\n")
        return

    targets = []
    if args.url:
        targets.append(args.url)
    if args.targets:
        for t in args.targets:
            if os.path.isfile(t):
                with open(t, "r", encoding="utf-8") as f:
                    targets += [line.strip() for line in f if line.strip()]
            else:
                targets.append(t.strip())

    if not targets:
        print(Fore.RED + "[-] No targets specified. Use -u or pass a file.")
        return

    threads = []
    for tgt in targets:
        t = threading.Thread(target=full_recon, args=(tgt, args.proxy, args.profile, args.threads, args.export_csv, args.html_report, args.open))
        threads.append(t)
        t.start()
        if len(threads) >= args.threads:
            for th in threads:
                th.join()
            threads = []
    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
