#!/usr/bin/env python3
"""
Mustache Protocol Asset Extractor & Verification Tool
Dynamically discovers, validates, and downloads all assets from the official Google CDN.
Guarantees offline package integrity for PortMaster / muOS handhelds.
"""

import os
import re
import sys
import gzip
import argparse
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

def fetch_resource(url, timeout=20):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Handheld Linux; PortMaster)",
            "Accept-Encoding": "gzip, deflate"
        }
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        headers = dict(resp.headers)
        raw_data = resp.read()
        decompressed_data = decompress_if_gzip(raw_data)
        return decompressed_data, headers

def fetch_file(rel_path, force=False):
    dest = os.path.join(DEST_WWW, rel_path)
    if not force and os.path.exists(dest) and os.path.getsize(dest) > 0:
        return rel_path, True, "cached", os.path.getsize(dest)
    
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    full_url = BASE_URL.rstrip("/") + "/" + rel_path.lstrip("./")
    try:
        data, headers = fetch_resource(full_url)
        if len(data) == 0:
            return rel_path, False, "Empty file received", 0

        # Verify Content-Length if non-encoded and present
        cl = headers.get("Content-Length")
        ce = headers.get("Content-Encoding")
        if cl and not ce:
            try:
                expected_len = int(cl)
                if len(data) != expected_len:
                    return rel_path, False, f"Size mismatch: got {len(data)}, expected {expected_len}", len(data)
            except ValueError:
                pass

        with open(dest, "wb") as f:
            f.write(data)
        return rel_path, True, "downloaded", len(data)
    except Exception as e:
        return rel_path, False, str(e), 0

def discover_assets():
    """Dynamically parses index.html, JS bundles, and CSS manifests to discover all required assets."""
    print("[1/4] Discovering assets from index.html...")
    index_url = BASE_URL.rstrip("/") + "/index.html"
    try:
        html_bytes, _ = fetch_resource(index_url)
        html_text = html_bytes.decode("utf-8")
    except Exception as e:
        print(f"Error fetching index.html: {e}")
        sys.exit(1)

    os.makedirs(DEST_WWW, exist_ok=True)
    with open(os.path.join(DEST_WWW, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_text)

    discovered_files = set()

    # Extract <script src="...">
    for match in re.finditer(r'<script[^>]+src=["\']([^"\']+)["\']', html_text):
        src = match.group(1).lstrip("./")
        if not src.startswith("http"):
            discovered_files.add(src)

    # Extract <link href="...">
    for match in re.finditer(r'<link[^>]+href=["\']([^"\']+)["\']', html_text):
        href = match.group(1).lstrip("./")
        if not href.startswith("http"):
            discovered_files.add(href)

    # Download discovered CSS and JS core manifests first to parse deeper references
    js_bundles = [f for f in discovered_files if f.endswith(".js")]
    css_files = [f for f in discovered_files if f.endswith(".css")]

    print(f"      Discovered {len(js_bundles)} JS bundle(s) and {len(css_files)} CSS file(s).")
    for core_f in js_bundles + css_files:
        fetch_file(core_f)

    # Parse CSS files for font and asset url(...) declarations
    for css_rel in css_files:
        css_path = os.path.join(DEST_WWW, css_rel)
        if os.path.exists(css_path):
            with open(css_path, "r", encoding="utf-8", errors="ignore") as f:
                css_content = f.read()
            css_dir = os.path.dirname(css_rel)
            for url_match in re.finditer(r'url\(["\']?([^"\'\)]+)["\']?\)', css_content):
                u = url_match.group(1).split("?")[0].split("#")[0].lstrip("./")
                if not u.startswith("http") and not u.startswith("data:"):
                    resolved = os.path.normpath(os.path.join(css_dir, u)) if css_dir else u
                    discovered_files.add(resolved)

    # Parse JS bundles for asset paths
    for js_rel in js_bundles:
        js_path = os.path.join(DEST_WWW, js_rel)
        if os.path.exists(js_path):
            with open(js_path, "r", encoding="utf-8", errors="ignore") as f:
                js_content = f.read()
            matches = re.findall(r"assets/[a-zA-Z0-9_\-\.\/]+", js_content)
            for m in matches:
                clean_m = m.rstrip(".,;:)\x22\x27`")
                if "." in os.path.basename(clean_m):
                    discovered_files.add(clean_m)

    # Always ensure critical intro video is tracked
    discovered_files.add("assets/videos/intro-cutscene-en.mp4")

    return sorted(list(discovered_files))

def verify_local_assets(all_files):
    print("\n[Verification] Checking local asset files integrity...")
    missing = []
    zero_byte = []
    total_size = 0

    for rel_path in all_files:
        dest = os.path.join(DEST_WWW, rel_path)
        if not os.path.exists(dest):
            missing.append(rel_path)
        else:
            sz = os.path.getsize(dest)
            if sz == 0:
                zero_byte.append(rel_path)
            total_size += sz

    print(f"  Total assets tracked: {len(all_files)}")
    print(f"  Total local size:     {total_size / (1024*1024):.2f} MB")
    if missing:
        print(f"  [ERROR] {len(missing)} missing files!")
        for m in missing[:5]:
            print(f"    - {m}")
    if zero_byte:
        print(f"  [ERROR] {len(zero_byte)} empty (0-byte) files!")
        for z in zero_byte[:5]:
            print(f"    - {z}")

    return len(missing) == 0 and len(zero_byte) == 0

def main():
    parser = argparse.ArgumentParser(description="Mustache Protocol Asset Tool")
    parser.add_argument("--verify-only", action="store_true", help="Only verify integrity of existing files")
    parser.add_argument("--force", action="store_true", help="Force re-download of all assets")
    parser.add_argument("--workers", type=int, default=12, help="Number of concurrent download threads")
    args = parser.parse_args()

    print("=" * 65)
    print(" Mustache Protocol: Dynamic Asset Discovery & Integrity Tool")
    print(f" Target Directory: {DEST_WWW}")
    print("=" * 65)

    all_files = discover_assets()

    if args.verify_only:
        ok = verify_local_assets(all_files)
        sys.exit(0 if ok else 1)

    print(f"\n[2/4] Downloading {len(all_files)} assets in parallel (threads: {args.workers})...")
    failed = []
    downloaded_count = 0
    cached_count = 0

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(fetch_file, f, args.force): f for f in all_files}
        done = 0
        for fut in as_completed(futures):
            rel_path, ok, info, sz = fut.result()
            done += 1
            if ok:
                if info == "cached":
                    cached_count += 1
                else:
                    downloaded_count += 1
            else:
                failed.append((rel_path, info))

            if done % 50 == 0 or done == len(all_files):
                print(f"  Progress: {done}/{len(all_files)} files evaluated...")

    print(f"\n[3/4] Download Summary:")
    print(f"  - Cached:     {cached_count}")
    print(f"  - Downloaded: {downloaded_count}")
    print(f"  - Failed:     {len(failed)}")

    # Verify after sync
    print("\n[4/4] Verifying complete directory integrity...")
    integrity_ok = verify_local_assets(all_files)

    if failed or not integrity_ok:
        print("\n[FAILED] One or more assets failed to download or verify:")
        for rel_path, err in failed:
            print(f"  ! {rel_path}: {err}")
        sys.exit(1)

    print("\n[SUCCESS] All assets successfully validated and stored in mustacheprotocol/www/")
    sys.exit(0)

if __name__ == "__main__":
    main()
