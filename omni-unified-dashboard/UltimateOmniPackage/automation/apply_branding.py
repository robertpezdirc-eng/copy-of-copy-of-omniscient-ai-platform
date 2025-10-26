import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "brand_config.json"
WEB_DIR = ROOT / "web"
CSS_BRAND = WEB_DIR / "assets" / "css" / "brand.css"

HTML_META_RE = {
    "title": re.compile(r"<title>.*?</title>", re.I | re.S),
    "description": re.compile(r"<meta[^>]*name=\"description\"[^>]*content=\".*?\"[^>]*>", re.I | re.S),
    "keywords": re.compile(r"<meta[^>]*name=\"keywords\"[^>]*content=\".*?\"[^>]*>", re.I | re.S),
}

def normalize_logo_path(logo_path: str) -> str:
    # Convert config path to relative from web HTML files
    # If it contains '/web/', strip up to that
    parts = logo_path.replace("\\", "/")
    if "/web/" in parts:
        parts = parts.split("/web/", 1)[1]
    return parts

def apply_brand_css(cfg: dict):
    css = (
        "/* Generated from config/brand_config.json */\n"
        ":root {\n"
        f"  --accent: {cfg.get('primary_color', '#1e90ff')};\n"
        f"  --ok: {cfg.get('secondary_color', '#22c55e')};\n"
        f"  --highlight: {cfg.get('accent_color', '#ff9800')};\n"
        "}\n"
    )
    CSS_BRAND.parent.mkdir(parents=True, exist_ok=True)
    CSS_BRAND.write_text(css, encoding="utf-8")
    print(f"Wrote brand CSS -> {CSS_BRAND}")

def patch_html(file_path: Path, cfg: dict):
    html = file_path.read_text(encoding="utf-8")

    site_name = cfg.get("seo", {}).get("site_name", "Ultimate Omni Package")
    desc = cfg.get("seo", {}).get("default_description", "")
    keywords = ", ".join(cfg.get("seo", {}).get("default_keywords", []))
    logo_rel = normalize_logo_path(cfg.get("logo_path", "assets/img/placeholder.svg"))

    # Title
    html = HTML_META_RE["title"].sub(f"<title>{site_name}</title>", html)

    # Description
    if HTML_META_RE["description"].search(html):
        html = HTML_META_RE["description"].sub(
            f'<meta name="description" content="{desc}" />', html
        )
    else:
        html = html.replace(
            "</head>", f'  <meta name="description" content="{desc}" />\n</head>'
        )

    # Keywords
    if keywords:
        if HTML_META_RE["keywords"].search(html):
            html = HTML_META_RE["keywords"].sub(
                f'<meta name="keywords" content="{keywords}" />', html
            )
        else:
            html = html.replace(
                "</head>", f'  <meta name="keywords" content="{keywords}" />\n</head>'
            )

    # Logo <img src="...">
    html = re.sub(
        r"<img\s+src=\"assets/img/[^\"]+\"",
        f'<img src="{logo_rel}"',
        html,
        flags=re.I,
    )

    file_path.write_text(html, encoding="utf-8")
    print(f"Patched HTML -> {file_path}")


def main():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    apply_brand_css(cfg)

    # Patch all html files in web/
    for html_file in WEB_DIR.glob("*.html"):
        patch_html(html_file, cfg)

if __name__ == "__main__":
    main()