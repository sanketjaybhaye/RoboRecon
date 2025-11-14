#!/usr/bin/env python3
"""
RoboRecon v6.0 - Smart Recon Upgrade
- smart sitemap discovery (/sitemap.xml, sitemap_index.xml, sitemap*.xml, sitemap.txt)
- small built-in wordlist for hidden URL guessing (fast, low-noise)
- keeps previous features (robots parsing, sitemap crawl, gzip, html report)
Author: Sanket Jaybhaye
"""
import argparse, os, re, json, time, random, threading, csv, webbrowser, io, gzip, html, sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
try:
    import requests
    from lxml import etree
    from colorama import Fore, init
    init(autoreset=True)
except Exception:
    print("Missing dependencies. Use setup.sh to install requests, lxml, colorama.")
    raise

USER_AGENT = "RoboRecon/6.0 (+https://github.com/sanketjaybhaye)"
BASE_OUTPUT = "recon_reports"
os.makedirs(BASE_OUTPUT, exist_ok=True)
lock = threading.Lock()

SMALL_WORDLIST = [
    "admin/", "administrator/", "login", "user/login", "wp-admin/", "cpanel/", "panel/",
    "backup.zip", "backup.tar.gz", "db_backup.sql", "uploads/", "dev/", "test/", "old/", "staging/"
]

COMMON_SITEMAP_LOCATIONS = [
    "/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml", "/sitemap1.xml",
    "/sitemap/sitemap-index.xml", "/sitemap.xml.gz", "/sitemap_index.xml.gz", "/sitemap.txt"
]

TEMPLATE_CSS = """
body{font-family:Inter,Segoe UI,Helvetica,Arial,sans-serif;margin:18px;color:#111}
.container{max-width:1100px;margin:auto}
h1{font-size:20px}
table{width:100%;border-collapse:collapse;margin-top:12px}
th,td{padding:8px;border-bottom:1px solid #ddd;text-align:left}
.small{font-size:12px;color:#666}
pre{background:#f7f7f9;padding:10px;border-radius:6px;overflow:auto}
a{color:#0366d6}
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
      if (dir == "asc") { if (x.innerText.toLowerCase() > y.innerText.toLowerCase()) { shouldSwitch= true; break; } }
      else { if (x.innerText.toLowerCase() < y.innerText.toLowerCase()) { shouldSwitch = true; break; } }
    }
    if (shouldSwitch) { rows[i].parentNode.insertBefore(rows[i + 1], rows[i]); switching = true; switchcount ++; }
    else { if (switchcount == 0 && dir == "asc") { dir = "desc"; switching = true; } }
  }
}
"""

def ts():
    return datetime.now().strftime("[%H:%M:%S]")

def fetch_content(url, proxy=None, timeout=10):
    try:
        proxies = {"http": proxy, "https": proxy} if proxy else None
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, proxies=proxies, timeout=timeout, stream=True)
        r.raise_for_status()
        raw = r.raw.read()
        if url.lower().endswith(".gz") or (len(raw) >= 2 and raw[:2] == b"\x1f\x8b"):
            try:
                raw = gzip.decompress(raw)
            except Exception:
                buf = io.BytesIO(raw)
                try:
                    with gzip.GzipFile(fileobj=buf) as gz:
                        raw = gz.read()
                except Exception:
                    pass
        enc = r.encoding or "utf-8"
        return raw.decode(enc, errors="replace")
    except Exception:
        return None

def parse_robots(content):
    return {
        "disallow": re.findall(r"(?im)^\s*Disallow\s*:\s*(.*)$", content),
        "allow": re.findall(r"(?im)^\s*Allow\s*:\s*(.*)$", content),
        "sitemaps": re.findall(r"(?im)^\s*Sitemap\s*:\s*(.*)$", content),
        "comments": re.findall(r"(?m)#\s*(.*)$", content)
    }

def extract_sitemap_urls(content):
    urls = []
    try:
        root = etree.fromstring(content.encode("utf-8"))
        for loc in root.findall(".//{*}loc"):
            if loc is not None and loc.text:
                urls.append(loc.text.strip())
    except Exception:
        for line in content.splitlines():
            line = line.strip()
            if line and (line.startswith("http://") or line.startswith("https://")):
                urls.append(line)
    return urls

def analyze_sitemaps(sitemaps, proxy=None, recursive=True):
    all_urls = []
    for sm in sitemaps:
        txt = fetch_content(sm, proxy)
        if not txt:
            continue
        urls = extract_sitemap_urls(txt)
        all_urls.extend(urls)
        if recursive:
            nested = [u for u in urls if u.lower().endswith(".xml") or "sitemap" in u.lower()]
            if nested:
                try:
                    all_urls.extend(analyze_sitemaps(nested, proxy, recursive=True))
                except Exception:
                    pass
    return list(dict.fromkeys(all_urls))

def check_head(url, proxy=None, timeout=6):
    try:
        proxies = {"http": proxy, "https": proxy} if proxy else None
        r = requests.head(url, headers={"User-Agent": USER_AGENT}, proxies=proxies, timeout=timeout, allow_redirects=True)
        return r.status_code, r.headers.get("Content-Type")
    except Exception as e:
        return None, str(e)

def save_report(domain, data, export_csv=False, html_report=False, auto_open=False):
    tsf = datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_path = os.path.join(BASE_OUTPUT, domain, tsf)
    os.makedirs(dir_path, exist_ok=True)
    json_path = os.path.join(dir_path, "report.json")
    txt_path = os.path.join(dir_path, "report.txt")
    csv_path = os.path.join(dir_path, "urls.csv")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"=== RoboRecon v6 Report: {domain} ===\n\n")
        for k, v in data.items():
            f.write(f"[{k.upper()}] ({len(v) if isinstance(v, list) else 1})\n")
            if isinstance(v, list):
                for i in v:
                    f.write(f"  - {i}\n")
            else:
                f.write(f"  {v}\n")
            f.write("\n")
    if export_csv and data.get("found_urls"):
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["url","status","content_type"])
            for item in data.get("found_urls"):
                writer.writerow([item.get("url"), item.get("status"), item.get("content_type")])
    print(Fore.GREEN + f"{ts()} [+] Reports saved under: {dir_path}")
    if html_report:
        try:
            html_path = generate_html_report(json_path)
            print(Fore.GREEN + f"{ts()} [+] HTML report: {html_path}")
            if auto_open:
                webbrowser.open("file://" + os.path.abspath(html_path))
        except Exception as e:
            print(Fore.YELLOW + f"{ts()} [!] HTML generation failed: {e}")
    elif auto_open:
        try:
            webbrowser.open("file://" + os.path.abspath(txt_path))
        except Exception:
            pass

def smart_sitemap_discovery(base_url, proxy=None):
    found = []
    for loc in COMMON_SITEMAP_LOCATIONS:
        candidate = base_url.rstrip("/") + loc
        txt = fetch_content(candidate, proxy)
        if txt:
            found.append(candidate)
    return list(dict.fromkeys(found))

def find_hidden_paths(base_url, proxy=None, wordlist=None, threads=8, per_domain_delay=0.2):
    wl = wordlist or SMALL_WORDLIST
    base = base_url.rstrip("/") + "/"
    results = []
    def worker(path):
        url = requests.compat.urljoin(base, path)
        status, ctype = check_head(url, proxy)
        return {"url": url, "status": status, "content_type": ctype}
    with ThreadPoolExecutor(max_workers=threads) as ex:
        futures = {ex.submit(worker, w): w for w in wl}
        for fut in as_completed(futures):
            try:
                r = fut.result()
                results.append(r)
            except Exception:
                results.append({"url": requests.compat.urljoin(base, futures[fut]), "status": None})
            time.sleep(per_domain_delay * random.random())
    # keep interesting ones (2xx,3xx,4xx)
    positives = [r for r in results if r.get("status") and str(r.get("status")).startswith(("2","3","4"))]
    return results, positives

def generate_html_report(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    base = os.path.splitext(json_path)[0]
    out = base + ".html"
    title = f"RoboRecon v6 — {os.path.basename(json_path)}"
    now = datetime.now().isoformat()
    parts = []
    parts.append(f"<html><head><meta charset='utf-8'><title>{html.escape(title)}</title><style>{TEMPLATE_CSS}</style></head><body><div class='container'>")
    parts.append(f"<h1>{html.escape(title)}</h1><div class='small'>generated: {now}</div>")
    robots = data.get("robots")
    if robots:
        parts.append("<div class='section'><h2>robots.txt</h2>")
        parts.append(f"<pre>{html.escape(robots)}</pre></div>")
    for key in ("disallow","allow","comments"):
        vals = data.get(key, [])
        parts.append(f"<div class='section'><h2>{key.upper()} ({len(vals)})</h2>")
        if vals:
            parts.append("<ul>")
            for v in vals:
                parts.append(f"<li>{html.escape(str(v))}</li>")
            parts.append("</ul>")
        else:
            parts.append("<div class='small'>(none)</div>")
        parts.append("</div>")
    sitemaps = data.get("sitemaps") or data.get("discovered_sitemaps") or []
    discovered = data.get("sitemap_urls") or data.get("discovered_urls") or []
    parts.append(f"<div class='section'><h2>Sitemaps ({len(sitemaps)})</h2>")
    if sitemaps:
        parts.append("<ul>")
        for s in sitemaps:
            parts.append(f"<li><a href='{html.escape(s)}' target='_blank'>{html.escape(s)}</a></li>")
        parts.append("</ul>")
    else:
        parts.append("<div class='small'>(none)</div>")
    parts.append("</div>")
    parts.append(f"<div class='section'><h2>Discovered URLs ({len(discovered)})</h2>")
    if discovered:
        parts.append("<table id='urls'><thead><tr><th onclick=\"sortTable(0,'urls')\">URL</th></tr></thead><tbody>")
        for u in discovered:
            parts.append(f"<tr><td><a href='{html.escape(u)}' target='_blank'>{html.escape(u)}</a></td></tr>")
        parts.append("</tbody></table>")
    else:
        parts.append("<div class='small'>(none)</div>")
    parts.append("</div>")
    found = data.get("found_urls") or []
    parts.append(f"<div class='section'><h2>Found Hidden Paths ({len(found)})</h2>")
    if found:
        parts.append("<table id='found'><thead><tr><th>URL</th><th>Status</th><th>Content-Type</th></tr></thead><tbody>")
        for fitem in found:
            parts.append(f"<tr><td><a href='{html.escape(fitem.get('url'))}' target='_blank'>{html.escape(fitem.get('url'))}</a></td><td>{html.escape(str(fitem.get('status')))}</td><td>{html.escape(str(fitem.get('content_type') or ''))}</td></tr>")
        parts.append("</tbody></table>")
    else:
        parts.append("<div class='small'>(none)</div>")
    parts.append("</div>")
    parts.append("<div class='section'><h2>Raw JSON</h2><pre>")
    parts.append(html.escape(json.dumps(data, indent=2)))
    parts.append("</pre></div>")
    parts.append(f"</div><script>{TEMPLATE_JS}</script></body></html>")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    return out

def recon_target(target, proxy=None, deep=False, crawl_sitemaps=False, scan_urls=False, export_csv=False, html_report=False, auto_open=False, threads=4):
    with lock:
        print(Fore.CYAN + f"{ts()} [*] Starting recon on {target}")
    if not target.startswith("http"):
        target = "https://" + target
    if not target.endswith("/"):
        target += "/"
    result = {"target": target, "disallow": [], "allow": [], "sitemaps": [], "comments": []}
    robots_url = target + "robots.txt"
    content = fetch_content(robots_url, proxy)
    if content:
        parsed = parse_robots(content)
        result.update(parsed)
        result["robots"] = content
        print(Fore.GREEN + f"{ts()} [+] robots.txt parsed")
    else:
        print(Fore.YELLOW + f"{ts()} [!] robots.txt not found or unreachable.")
    # smart sitemap discovery if robots didn't list sitemaps or deep
    discovered_sitemaps = result.get("sitemaps", []) or []
    if deep and not discovered_sitemaps:
        discovered_sitemaps = smart_sitemap_discovery(target, proxy)
        if discovered_sitemaps:
            result["discovered_sitemaps"] = discovered_sitemaps
            print(Fore.GREEN + f"{ts()} [+] discovered {len(discovered_sitemaps)} sitemap candidates via heuristics")
    if crawl_sitemaps or (deep and discovered_sitemaps):
        sitemaps_to_crawl = result.get("sitemaps", []) + result.get("discovered_sitemaps", [])
        sitemaps_to_crawl = list(dict.fromkeys([s for s in sitemaps_to_crawl if s]))
        if sitemaps_to_crawl:
            print(Fore.CYAN + f"{ts()} [*] crawling {len(sitemaps_to_crawl)} sitemaps")
            sitemap_urls = analyze_sitemaps(sitemaps_to_crawl, proxy, recursive=True)
            result["sitemap_urls"] = sitemap_urls
            print(Fore.GREEN + f"{ts()} [+] extracted {len(sitemap_urls)} URLs from sitemaps")
    # scan sample URLs if asked
    if scan_urls and result.get("sitemap_urls"):
        sample = random.sample(result["sitemap_urls"], min(10, len(result["sitemap_urls"])))
        checked = []
        for u in sample:
            status, ctype = check_head(u, proxy)
            checked.append({"url": u, "status": status, "content_type": ctype})
            print(Fore.WHITE + f"   {u} -> {status}")
        result["checked_urls"] = checked
    # deep hidden-path guessing
    found_urls = []
    if deep:
        print(Fore.CYAN + f"{ts()} [*] running hidden path wordlist (fast mode)")
        all_results, positives = find_hidden_paths(target, proxy, SMALL_WORDLIST, threads=threads)
        result["found_urls"] = all_results
        result["found_urls_positive"] = positives
        print(Fore.GREEN + f"{ts()} [+] found {len(positives)} likely interesting paths")
    save_report_name = target.replace("https://","").replace("http://","").strip("/").replace("/","_")
    save_report(save_report_name, result, export_csv, html_report, auto_open)

def save_report(domain, data, export_csv=False, html_report=False, auto_open=False):
    save_report.__wrapped__ = save_report  # noop for compatibility
    # use save_report function previously defined (wrapping for reuse)
    # simple redirection to existing implementation
    # implement inline to avoid complex imports
    tsf = datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_path = os.path.join(BASE_OUTPUT, domain, tsf)
    os.makedirs(dir_path, exist_ok=True)
    json_path = os.path.join(dir_path, "report.json")
    txt_path = os.path.join(dir_path, "report.txt")
    csv_path = os.path.join(dir_path, "urls.csv")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"=== RoboRecon v6 Report: {domain} ===\n\n")
        for k, v in data.items():
            if isinstance(v, list):
                f.write(f"[{k.upper()}] ({len(v)})\n")
                for i in v:
                    f.write(f"  - {i}\n")
            else:
                f.write(f"[{k.upper()}]\n  {v}\n")
            f.write("\n")
    if export_csv and data.get("found_urls"):
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["url","status","content_type"])
            for item in data.get("found_urls"):
                writer.writerow([item.get("url"), item.get("status"), item.get("content_type")])
    print(Fore.GREEN + f"{ts()} [+] Reports saved under: {dir_path}")
    if html_report:
        try:
            html_path = generate_html_report(json_path)
            print(Fore.GREEN + f"{ts()} [+] HTML report: {html_path}")
            if auto_open:
                try:
                    webbrowser.open("file://" + os.path.abspath(html_path))
                except Exception:
                    pass
        except Exception as e:
            print(Fore.YELLOW + f"{ts()} [!] HTML generation failed: {e}")
    elif auto_open:
        try:
            webbrowser.open("file://" + os.path.abspath(txt_path))
        except Exception:
            pass

def main():
    p = argparse.ArgumentParser(prog="RoboRecon v6")
    p.add_argument("-u","--url",help="Target domain or URL")
    p.add_argument("targets",nargs="*",help="Targets or file containing list")
    p.add_argument("--proxy",help="Proxy/Tor e.g. socks5h://127.0.0.1:9050")
    p.add_argument("--threads",type=int,default=6,help="Worker threads")
    p.add_argument("--deep",action="store_true",help="Deep mode: sitemap discovery + hidden path checks")
    p.add_argument("--crawl-sitemaps",action="store_true",help="Explicitly crawl sitemaps found in robots")
    p.add_argument("--scan-urls",action="store_true",help="Check status of discovered URLs")
    p.add_argument("--export-csv",action="store_true",help="Export found URLs to CSV")
    p.add_argument("--html-report",action="store_true",help="Generate HTML dashboard next to JSON")
    p.add_argument("--open",action="store_true",help="Open report after generation")
    args = p.parse_args()
    # compile targets
    targets = []
    if args.url:
        targets.append(args.url)
    if args.targets:
        for t in args.targets:
            if os.path.isfile(t):
                with open(t,"r",encoding="utf-8") as f:
                    targets += [line.strip() for line in f if line.strip()]
            else:
                targets.append(t.strip())
    if not targets:
        print(Fore.RED + "[-] No targets specified. Use -u or pass a file.")
        return
    threads = []
    for tgt in targets:
        t = threading.Thread(target=recon_target, args=(tgt, args.proxy, args.deep, args.crawl_sitemaps, args.scan_urls, args.export_csv, args.html_report, args.open, args.threads))
        threads.append(t)
        t.start()
        if len(threads) >= args.threads:
            for th in threads:
                th.join()
            threads = []
    for t in threads:
        t.join()
    print(Fore.GREEN + f"\n{ts()} [✓] Recon complete for all targets.\n")

if __name__ == "__main__":
    main()
