#!/usr/bin/env python3
import argparse
import os
import sys
import urllib.request
import urllib.error
import urllib.parse
import io
import json
import gzip
from datetime import datetime
import xml.etree.ElementTree as ET

def normalize_url(u):
    if not (u.startswith("http://") or u.startswith("https://")):
        u = "https://" + u
    parsed = urllib.parse.urlparse(u)
    if not parsed.path:
        u = u if u.endswith("/") else u + "/"
    return u

def fetch_bytes(url, user_agent, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(), resp.getheader("Content-Type", "")

def fetch_text(url, user_agent, timeout):
    raw, ctype = fetch_bytes(url, user_agent, timeout)
    if url.lower().endswith(".gz") or b"\x1f\x8b" in raw[:2]:
        try:
            raw = gzip.decompress(raw)
        except Exception:
            pass
    charset = "utf-8"
    if "charset=" in ctype:
        charset = ctype.split("charset=")[-1].split(";")[0].strip()
    return raw.decode(charset, errors="replace")

def extract_sitemaps(robots_text):
    lines = robots_text.splitlines()
    sm = []
    for ln in lines:
        ln_stripped = ln.strip()
        if ln_stripped.lower().startswith("sitemap:"):
            parts = ln_stripped.split(":", 1)
            if len(parts) > 1:
                sm_url = parts[1].strip()
                sm.append(sm_url)
    return sm

def parse_sitemap_xml(xml_text, base_url=None, max_urls=None):
    urls = []
    try:
        root = ET.fromstring(xml_text.encode("utf-8"))
    except Exception:
        return urls
    tag = root.tag.lower()
    if tag.endswith("sitemapindex"):
        for s in root.findall(".//{*}sitemap/{*}loc"):
            if s is not None and s.text:
                urls.append(s.text.strip())
                if max_urls and len(urls) >= max_urls:
                    break
    else:
        for u in root.findall(".//{*}url/{*}loc"):
            if u is not None and u.text:
                urls.append(u.text.strip())
                if max_urls and len(urls) >= max_urls:
                    break
    return urls

def save_output(domain_label, content, out_dir, kind="robots"):
    if not out_dir:
        return None
    os.makedirs(out_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{domain_label}_{kind}_{timestamp}.txt"
    path = os.path.join(out_dir, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path

def process_target(target, user_agent, timeout, out_dir, crawl_sitemaps, max_urls_per_sitemap, max_urls_total, verbose):
    summary = {"target": target, "robots_fetched": False, "robots_path": None, "sitemaps": [], "discovered_urls": []}
    try:
        base = normalize_url(target)
    except Exception as e:
        summary["error"] = f"invalid url: {e}"
        return summary
    robots_url = urllib.parse.urljoin(base, "robots.txt")
    try:
        robots_text = fetch_text(robots_url, user_agent, timeout)
        summary["robots_fetched"] = True
        summary["robots_path"] = save_output(urllib.parse.urlparse(base).netloc.replace(":", "_") or "target", robots_text, out_dir, kind="robots")
        if verbose:
            print(f"[+] fetched robots.txt for {target} ({len(robots_text)} bytes)")
    except urllib.error.HTTPError as e:
        summary["error"] = f"http_error {e.code}"
        return summary
    except urllib.error.URLError as e:
        summary["error"] = f"url_error {e.reason}"
        return summary
    except Exception as e:
        summary["error"] = str(e)
        return summary

    sitemaps = extract_sitemaps(robots_text)
    summary["sitemaps"] = [{"loc": s, "fetched": False, "urls_count": 0, "path": None, "error": None} for s in sitemaps]

    if crawl_sitemaps and sitemaps:
        total_collected = 0
        for sm in summary["sitemaps"]:
            if max_urls_total and total_collected >= max_urls_total:
                break
            sm_url = sm["loc"]
            try:
                xml_text = fetch_text(sm_url, user_agent, timeout)
                sm["fetched"] = True
                sm["path"] = save_output(urllib.parse.urlparse(sm_url).netloc.replace(":", "_") or "sitemap", xml_text, out_dir, kind="sitemap")
                urls = parse_sitemap_xml(xml_text, base_url=base, max_urls=max_urls_per_sitemap)
                to_take = urls
                if max_urls_total:
                    remaining = max_urls_total - total_collected
                    to_take = urls[:remaining]
                sm["urls_count"] = len(to_take)
                summary["discovered_urls"].extend(to_take)
                total_collected += len(to_take)
                if verbose:
                    print(f"[+] parsed sitemap {sm_url} -> {len(to_take)} urls")
                # handle nested sitemapindex entries: if urls appear to be sitemap links and we still have budget, fetch them
                if sm["urls_count"] == 0 and xml_text and "<sitemapindex" in xml_text.lower():
                    nested = parse_sitemap_xml(xml_text, base_url=base, max_urls=max_urls_per_sitemap)
                    for n in nested:
                        if max_urls_total and total_collected >= max_urls_total:
                            break
                        try:
                            nested_text = fetch_text(n, user_agent, timeout)
                            nested_urls = parse_sitemap_xml(nested_text, base_url=base, max_urls=max_urls_per_sitemap)
                            take = nested_urls
                            if max_urls_total:
                                remaining = max_urls_total - total_collected
                                take = nested_urls[:remaining]
                            summary["discovered_urls"].extend(take)
                            total_collected += len(take)
                            if verbose:
                                print(f"[+] parsed nested sitemap {n} -> {len(take)} urls")
                        except Exception:
                            continue
            except Exception as e:
                sm["error"] = str(e)
                if verbose:
                    print(f"[-] failed sitemap {sm_url} -> {e}")
    return summary

def main():
    p = argparse.ArgumentParser(prog="robots_recon", description="Fetch robots.txt, detect and crawl sitemaps")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", "-u", help="Target URL (e.g. https://example.com or example.com)")
    group.add_argument("--input-file", "-i", help="File with list of targets (one per line)")
    p.add_argument("--user-agent", "-a", default="RobotsRecon/2.0 (+https://example.local)", help="User-Agent header")
    p.add_argument("--timeout", "-t", type=float, default=10.0, help="Request timeout seconds")
    p.add_argument("--output-dir", "-o", default="robots_output", help="Directory to save files (set '' to disable)")
    p.add_argument("--crawl-sitemaps", action="store_true", help="Fetch and parse sitemaps found in robots.txt")
    p.add_argument("--max-urls-per-sitemap", type=int, default=0, help="Limit URLs taken from each sitemap (0 = no limit)")
    p.add_argument("--max-urls-total", type=int, default=0, help="Limit total URLs discovered per target (0 = no limit)")
    p.add_argument("--output-json", "-j", help="Write full JSON summary to this file")
    p.add_argument("--quiet", "-q", action="store_true", help="Minimal output")
    args = p.parse_args()

    targets = []
    if args.url:
        targets = [args.url.strip()]
    else:
        try:
            with open(args.input_file, "r", encoding="utf-8") as f:
                targets = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
        except Exception as e:
            print("Failed to read input file:", e, file=sys.stderr)
            sys.exit(2)

    out_dir = args.output_dir if args.output_dir != "" else None
    results = []
    for t in targets:
        r = process_target(t, args.user_agent, args.timeout, out_dir, args.crawl_sitemaps, args.max_urls_per_sitemap or None, args.max_urls_total or None, verbose=not args.quiet)
        results.append(r)

    if not args.quiet:
        print("\nSummary")
        for r in results:
            if r.get("robots_fetched"):
                print(f" - {r['target']}: robots OK, sitemaps={len(r['sitemaps'])}, discovered_urls={len(r['discovered_urls'])}")
            else:
                print(f" - {r['target']}: FAILED -> {r.get('error')}")
    if args.output_json:
        try:
            with open(args.output_json, "w", encoding="utf-8") as jf:
                json.dump({"generated_at": datetime.now().isoformat(), "results": results}, jf, indent=2, ensure_ascii=False)
            if not args.quiet:
                print(f"[+] JSON summary written to {args.output_json}")
        except Exception as e:
            print("Failed to write JSON:", e, file=sys.stderr)

if __name__ == "__main__":
    main()
