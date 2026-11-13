#!/usr/bin/env python3
"""
Mustache Protocol Asset Extractor & Offline Package Builder
Downloads all original assets directly from the official Google CDN
and builds the PortMaster / muOS offline directory structure.
"""

import os
import re
import sys
import gzip
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://mustacheprotocol.withgoogle.com/"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DEST_WWW = os.path.join(REPO_ROOT, "mustacheprotocol", "www")

def decompress_if_gzip(data):
    if len(data) >= 2 and data[0] == 0x1f and data[1] == 0x8b:
        try:
            return gzip.decompress(data)
        except Exception:
            return data
    return data

def fetch_file(rel_path):
    dest = os.path.join(DEST_WWW, rel_path)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return rel_path, True, "cached"
    
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    req = urllib.request.Request(
        BASE_URL + rel_path,
        headers={
            "User-Agent": "Mozilla/5.0 (Handheld Linux; PortMaster)",
            "Accept-Encoding": "gzip, deflate"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = decompress_if_gzip(resp.read())
            with open(dest, "wb") as f:
                f.write(data)
        return rel_path, True, len(data)
    except Exception as e:
        return rel_path, False, str(e)

def main():
    print("=" * 60)
    print("Mustache Protocol: Official CDN Asset Fetcher")
    print(f"Target Destination: {DEST_WWW}")
    print("=" * 60)

    # 1. Fetch index.html
    print("\n[1/3] Downloading index.html and core manifests...")
    req = urllib.request.Request(BASE_URL, headers={"User-Agent": "Mozilla/5.0", "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req) as resp:
        html = decompress_if_gzip(resp.read()).decode("utf-8")
    
    os.makedirs(DEST_WWW, exist_ok=True)
    with open(os.path.join(DEST_WWW, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    # 2. Extract asset references from main JS bundle
    core_files = [
        "fonts/fonts.css",
        "fonts/outfit-latin-ext.woff2",
        "fonts/outfit-latin.woff2",
        "fonts/press-start-2p-latin-ext.woff2",
        "fonts/press-start-2p-latin.woff2",
        "fonts/silkscreen-400-latin-ext.woff2",
        "fonts/silkscreen-400-latin.woff2",
        "fonts/silkscreen-700-latin-ext.woff2",
        "fonts/silkscreen-700-latin.woff2",
        "favicon.png",
        "apple-touch-icon.png",
        "assets/main-BBxYxh4e.css",
        "assets/main-BnlzpU15.js"
    ]

    for cf in core_files:
        fetch_file(cf)

    main_js_path = os.path.join(DEST_WWW, "assets", "main-BnlzpU15.js")
    with open(main_js_path, "r", encoding="utf-8") as f:
        js_text = f.read()

    asset_matches = set(re.findall(r"assets/[a-zA-Z0-9_\-\.\/]+", js_text))
    valid_assets = set()
    for a in asset_matches:
        a = a.rstrip(".,;:)\x22\x27`")
        if "." in os.path.basename(a):
            valid_assets.add(a)

    valid_assets.add("assets/videos/intro-cutscene-en.mp4")
    all_files = sorted(list(valid_assets | set(core_files)))

    # 3. Parallel download
    print(f"\n[2/3] Downloading {len(all_files)} assets in parallel...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_file, rel_path): rel_path for rel_path in all_files}
        done = 0
        for fut in as_completed(futures):
            rel_path, ok, info = fut.result()
            done += 1
            if done % 50 == 0 or done == len(all_files):
                print(f"  Downloaded {done}/{len(all_files)} files...")
            if not ok:
                print(f"  [Warning] Failed to fetch {rel_path}: {info}")

    print("\n[3/3] Done! All assets are stored locally in mustacheprotocol/www/")

if __name__ == "__main__":
    main()
