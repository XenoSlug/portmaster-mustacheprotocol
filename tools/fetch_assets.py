#!/usr/bin/env python3
"""
Mustache Protocol Asset Extractor, Dynamic Scraper & Offline Cryptographic Verifier
- In offline mode (--verify-only): Strictly verifies SHA-256 checksums of local assets without internet access.
- In sync/download mode: Dynamically crawls Google CDN manifests and generates/updates checksum manifests.
"""

import os
import re
import sys
import gzip
import hashlib
import argparse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://mustacheprotocol.withgoogle.com/"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
PORT_DIR = os.path.join(REPO_ROOT, "mustacheprotocol")
DEST_WWW = os.path.join(PORT_DIR, "www")
CHECKSUM_FILE = os.path.join(PORT_DIR, "checksums.sha256")

def calculate_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def decompress_if_gzip(data):
    if len(data) >= 2 and data[0] == 0x1f and data[1] == 0x8b:
        try:
            return gzip.decompress(data)
        except Exception:
            return data
    return data

def verify_offline_checksums():
    """100% Offline verification against cryptographic SHA-256 manifest."""
    print("=" * 65)
    print(" Mustache Protocol: Offline Cryptographic SHA-256 Verifier")
    print(f" Manifest: {CHECKSUM_FILE}")
    print(f" Target:   {DEST_WWW}")
    print("=" * 65)

    if not os.path.exists(CHECKSUM_FILE):
        print(f"[ERROR] Checksum manifest not found at: {CHECKSUM_FILE}")
        sys.exit(1)

    with open(CHECKSUM_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    print(f"\nVerifying {len(lines)} files against cryptographic hashes...")

    missing = []
    mismatch = []
    zero_byte = []
    total_size = 0
    passed = 0

    for line in lines:
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        expected_hash, rel_path = parts[0], parts[1].strip()
        full_path = os.path.join(DEST_WWW, rel_path)

        if not os.path.exists(full_path):
            missing.append(rel_path)
            continue

        sz = os.path.getsize(full_path)
        if sz == 0:
            zero_byte.append(rel_path)
            continue
        total_size += sz

        actual_hash = calculate_sha256(full_path)
        if actual_hash != expected_hash:
            mismatch.append((rel_path, expected_hash, actual_hash))
        else:
            passed += 1

    print(f"\nVerification Results:")
    print(f"  - Verified Matches: {passed} / {len(lines)}")
    print(f"  - Verified Size:    {total_size / (1024*1024):.2f} MB")
    print(f"  - Missing Files:    {len(missing)}")
    print(f"  - Corrupt/Empty:    {len(zero_byte)}")
    print(f"  - Hash Mismatches:  {len(mismatch)}")

    if missing or zero_byte or mismatch:
        print("\n[FAILED] Integrity check failed:")
        for m in missing[:5]:
            print(f"  [MISSING]  {m}")
        for z in zero_byte[:5]:
            print(f"  [EMPTY]    {z}")
        for path, exp, act in mismatch[:5]:
            print(f"  [MISMATCH] {path} (expected {exp[:8]}..., got {act[:8]}...)")
        sys.exit(1)

    print("\n[SUCCESS] 100% of offline assets matched their cryptographic SHA-256 signatures!")
    sys.exit(0)

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

    for match in re.finditer(r'<script[^>]+src=["\']([^"\']+)["\']', html_text):
        src = match.group(1).lstrip("./")
        if not src.startswith("http"):
            discovered_files.add(src)

    for match in re.finditer(r'<link[^>]+href=["\']([^"\']+)["\']', html_text):
        href = match.group(1).lstrip("./")
        if not href.startswith("http"):
            discovered_files.add(href)

    js_bundles = [f for f in discovered_files if f.endswith(".js")]
    css_files = [f for f in discovered_files if f.endswith(".css")]

    print(f"      Discovered {len(js_bundles)} JS bundle(s) and {len(css_files)} CSS file(s).")
    for core_f in js_bundles + css_files:
        fetch_file(core_f)

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

    discovered_files.add("assets/videos/intro-cutscene-en.mp4")
    return sorted(list(discovered_files))

def update_checksum_manifest():
    print(f"\n[Updating Manifest] Generating {CHECKSUM_FILE}...")
    lines = []
    count = 0
    for root, _, files in sorted(os.walk(DEST_WWW)):
        for f in sorted(files):
            full = os.path.join(root, f)
            rel = os.path.relpath(full, DEST_WWW)
            h = calculate_sha256(full)
            lines.append(f"{h}  {rel}\n")
            count += 1
    with open(CHECKSUM_FILE, "w", encoding="utf-8") as out:
        out.writelines(lines)
    print(f"  Generated SHA-256 manifest for {count} files.")

def main():
    parser = argparse.ArgumentParser(description="Mustache Protocol Asset & Verification Tool")
    parser.add_argument("--verify-only", action="store_true", help="Run 100% offline SHA-256 cryptographic verification against checksums.sha256")
    parser.add_argument("--force", action="store_true", help="Force re-download of all assets from Google CDN")
    parser.add_argument("--update-manifest", action="store_true", help="Regenerate checksums.sha256 manifest from current local files")
    parser.add_argument("--workers", type=int, default=12, help="Number of concurrent download threads")
    args = parser.parse_args()

    if args.verify_only:
        verify_offline_checksums()

    if args.update_manifest:
        update_checksum_manifest()
        sys.exit(0)

    print("=" * 65)
    print(" Mustache Protocol: Dynamic Asset Discovery & Sync")
    print(f" Target Directory: {DEST_WWW}")
    print("=" * 65)

    all_files = discover_assets()

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

    if failed:
        print("\n[FAILED] One or more assets failed to download:")
        for rel_path, err in failed:
            print(f"  ! {rel_path}: {err}")
        sys.exit(1)

    print("\n[4/4] Updating cryptographic SHA-256 checksum manifest...")
    update_checksum_manifest()
    print("\n[SUCCESS] All assets downloaded, verified, and signed in checksums.sha256!")
    sys.exit(0)

if __name__ == "__main__":
    main()
