#!/usr/bin/env python3
"""
RoboRecon v3 - Automated Robots.txt Intelligence Scanner
Author: MrRobot
Purpose: Fetch and analyze robots.txt for recon intelligence
"""

import urllib.request
import urllib.error
import re
import argparse
import json
import os
import threading
from xml.etree import ElementTree as ET
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

USER_AGENT = "RoboRecon/3.0 (+https://github.com/mrrobot)"
OUTPUT_DIR = "recon_reports"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_url(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(Fore.RED + f"[!] Failed to fetch {url}: {e}")
        return None

def parse_robots(content):
    data = {
        "disallow": re.findall(r"Disallow:\s*(.*)", content, re.I),
        "allow": re.findall(r"Allow:\s*(.*)", content, re.I),
        "sitemaps": re.findall(r"Sitemap:\s*(.*)", content, re.I),
        "comments": re.findall(r"#\s*(.*)", content)
    }
    return data

def analyze_sitemaps(sitemaps):
    urls = []
    for sitemap in sitemaps:
        content = fetch_url(sitemap)
        if not content:
            continue
        try:
            root = ET.fromstring(content)
            urls += [elem.text for elem in root.findall(".//{*}loc")]
        except Exception:
            print(Fore.YELLOW + f"[!] Could not parse sitemap XML: {sitemap}")
    return urls

def save_report(domain, data):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = os.path.join(OUTPUT_DIR, f"{domain}_{timestamp}.json")
    txt_file = os.path.join(OUTPUT_DIR, f"{domain}_{timestamp}.txt")

    with open(json_file, "w") as f:
        json.dump(data, f, indent=4)

    with open(txt_file, "w") as f:
        f.write(f"=== RoboRecon Report for {domain} ===\n\n")
        for key, value in data.items():
            f.write(f"[{key.upper()}]\n")
            if value:
                for item in value:
                    f.write(f"  - {item}\n")
            else:
                f.write("  (None)\n")
            f.write("\n")

    print(Fore.GREEN + f"[+] Reports saved: {json_file}, {txt_file}")

def recon_target(url):
    if not url.startswith("http"):
        url = "https://" + url

    if not url.endswith("/"):
        url += "/"

    robots_url = url + "robots.txt"
    print(Fore.CYAN + f"[*] Fetching {robots_url}")

    content = fetch_url(robots_url)
    if not content:
        print(Fore.RED + "[!] No robots.txt found or failed to fetch.")
        return

    parsed = parse_robots(content)
    print(Fore.GREEN + "[+] Robots.txt fetched successfully.")
    print(Fore.WHITE + f"  Disallowed: {len(parsed['disallow'])} | Allowed: {len(parsed['allow'])} | Sitemaps: {len(parsed['sitemaps'])}")

    if parsed["sitemaps"]:
        print(Fore.CYAN + "[*] Parsing Sitemaps for URLs...")
        sitemap_urls = analyze_sitemaps(parsed["sitemaps"])
        parsed["sitemap_urls"] = sitemap_urls
        print(Fore.GREEN + f"[+] Found {len(sitemap_urls)} URLs inside sitemaps.")

    save_report(url.replace("https://", "").replace("http://", "").strip("/"), parsed)

def main():
    parser = argparse.ArgumentParser(description="RoboRecon v3 - Automated Robots.txt Intelligence Scanner")
    parser.add_argument("target", nargs="+", help="Target domain(s) (example: google.com)")
    args = parser.parse_args()

    threads = []
    for target in args.target:
        t = threading.Thread(target=recon_target, args=(target,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
