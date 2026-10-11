"""Recompute the CSP hash of the inline theme script in site/index.html and write it into vercel.json.

    python scripts/update_csp_hash.py

Run this after editing the <script> block in the <head> of site/index.html; otherwise the browser will block it on Vercel
(the page would still work, but the saved theme would apply only after app.js loads, causing a brief flash).
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    html = (ROOT / "site" / "index.html").read_text(encoding="utf-8").replace("\r\n", "\n")  # git/Vercel serve LF
    scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
    if len(scripts) != 1:
        raise SystemExit(f"expected exactly 1 inline <script>, found {len(scripts)}")
    digest = "sha256-" + base64.b64encode(hashlib.sha256(scripts[0].encode("utf-8")).digest()).decode()

    path = ROOT / "vercel.json"
    cfg = json.loads(path.read_text(encoding="utf-8"))
    for rule in cfg["headers"]:
        for h in rule["headers"]:
            if h["key"] == "Content-Security-Policy":
                h["value"] = re.sub(r"'sha256-[^']+'", f"'{digest}'", h["value"])
    path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("CSP script hash:", digest)


if __name__ == "__main__":
    main()
