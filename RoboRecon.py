#!/usr/bin/env python3
"""
<<<<<<< HEAD
=======
RoboRecon v2 - Automated Robots.txt Intelligence Scanner
Author: Sanket Jaybhaye
Purpose: Fetch and analyze robots.txt for recon intelligence
>>>>>>> 04380b9a126874a84ac7ad37f9f67d58f12e1c59
"""

import requests, re, argparse, json, os, time, random, threading
from datetime import datetime
from colorama import Fore, Style, init
from lxml import etree

init(autoreset=True)

<<<<<<< HEAD
USER_AGENT = "RoboRecon/5.0 (+https://github.com/mrrobot)"
=======
USER_AGENT = "RoboRecon/3.0 (+https://github.com/sanketjaybhaye)"
>>>>>>> 04380b9a126874a84ac7ad37f9f67d58f12e1c59
OUTPUT_DIR = "recon_reports"
os.makedirs(OUTPUT_DIR, exist_ok=True)

lock = threading.Lock()

def timestamp():
    return datetime.now().strftime("[%H:%M:%S]")

def fetch_url(url, proxy=None):
    try:
        proxies = {"http": proxy, "https": proxy} if proxy else None
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, proxies=proxies, timeout=10)
        return r.text if r.status_code == 200 else None
    except Exception:
        return None

def parse_robots(content):
    return {
        "disallow": re.findall(r"Disallow:\s*(.*)", content, re.I),
        "allow": re.findall(r"Allow:\s*(.*)", content, re.I),
        "sitemaps": re.findall(r"Sitemap:\s*(.*)", content, re.I),
        "comments": re.findall(r"#\s*(.*)", content)
    }

def extract_sitemap_urls(sitemap_content):
    urls = []
    try:
        root = etree.fromstring(sitemap_content.encode("utf-8"))
        for loc in root.findall(".//{*}loc"):
            urls.append(loc.text.strip())
    except Exception:
        pass
    return urls

def analyze_sitemaps(sitemaps, proxy=None):
    all_urls = []
    for sm in sitemaps:
        data = fetch_url(sm, proxy)
        if not data:
            continue
        urls = extract_sitemap_urls(data)
        all_urls += urls
        nested = [u for u in urls if u.endswith(".xml")]
        if nested:
            all_urls += analyze_sitemaps(nested, proxy)
    return list(set(all_urls))

def check_url_status(url, proxy=None):
    try:
        proxies = {"http": proxy, "https": proxy} if proxy else None
        r = requests.head(url, headers={"User-Agent": USER_AGENT}, proxies=proxies, timeout=5, allow_redirects=True)
        return r.status_code
    except Exception:
        return None

def save_report(domain, data):
    timestamp_now = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.join(OUTPUT_DIR, f"{domain}_{timestamp_now}")
    with open(base + ".json", "w") as f:
        json.dump(data, f, indent=4)
    with open(base + ".txt", "w") as f:
        f.write(f"=== RoboRecon v5 Report: {domain} ===\n\n")
        for k, v in data.items():
            f.write(f"[{k.upper()}]\n")
            if isinstance(v, list):
                for i in v:
                    f.write(f"  - {i}\n")
            else:
                f.write(f"  {v}\n")
            f.write("\n")
    print(Fore.GREEN + f"{timestamp()} [+] Reports saved: {base}.json & {base}.txt")

def recon_target(target, proxy=None, delay=0.5):
    with lock:
        print(Fore.CYAN + f"{timestamp()} [*] Starting recon on {target}")
    if not target.startswith("http"):
        target = "https://" + target
    if not target.endswith("/"):
        target += "/"

    robots_url = target + "robots.txt"
    content = fetch_url(robots_url, proxy)
    if not content:
        print(Fore.RED + f"{timestamp()} [!] No robots.txt found for {target}")
        return

    parsed = parse_robots(content)
    print(Fore.GREEN + f"{timestamp()} [+] robots.txt fetched for {target}")

    sitemap_urls = []
    if parsed["sitemaps"]:
        print(Fore.CYAN + f"{timestamp()} [*] Parsing sitemaps for {target}")
        sitemap_urls = analyze_sitemaps(parsed["sitemaps"], proxy)
        parsed["sitemap_urls"] = sitemap_urls
        print(Fore.GREEN + f"{timestamp()} [+] Found {len(sitemap_urls)} sitemap URLs")

    if sitemap_urls:
        checked = []
        for u in random.sample(sitemap_urls, min(len(sitemap_urls), 10)):
            status = check_url_status(u, proxy)
            checked.append({"url": u, "status": status})
            print(Fore.WHITE + f"   {u} -> {status}")
            time.sleep(delay)
        parsed["checked_urls"] = checked

    save_report(target.replace("https://", "").replace("http://", "").strip("/"), parsed)

def main():
    parser = argparse.ArgumentParser(description="RoboRecon v5 - Final Recon Intelligence Framework")
    parser.add_argument("targets", nargs="+", help="Target domain(s) or file containing list")
    parser.add_argument("--proxy", help="Proxy or Tor (e.g. socks5h://127.0.0.1:9050)")
    parser.add_argument("--threads", type=int, default=2, help="Number of concurrent threads")
    args = parser.parse_args()

    targets = []
    for t in args.targets:
        if os.path.isfile(t):
            with open(t, "r") as f:
                targets += [line.strip() for line in f if line.strip()]
        else:
            targets.append(t.strip())

    threads = []
    for target in targets:
        t = threading.Thread(target=recon_target, args=(target, args.proxy))
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

