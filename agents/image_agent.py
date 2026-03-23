
import requests
import os
import re
import base64
from pathlib import Path


def _safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip())
    return cleaned.strip("_") or "generated_image"


def _placeholder_png() -> bytes:
    # 1x1 valid transparent PNG, used when network image fetch fails.
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO2Z4n0AAAAASUVORK5CYII="
    )


def _topic_slug(topic: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", ",", topic.strip()).strip(",").lower() or "nature"


def _provider_urls(topic: str):
    slug = _topic_slug(topic)
    return [
        f"https://loremflickr.com/800/600/{slug}",
        "https://picsum.photos/800/600",
    ]


def _extension_from_content_type(content_type: str) -> str:
    mapping = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }
    return mapping.get(content_type.lower(), ".jpg")


def _wikimedia_image_url(topic: str):
    """
    Search Wikimedia Commons and return a topic-relevant image URL.
    Uses thumbnail URLs for predictable file sizes and formats.
    """
    endpoint = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": topic,
        "gsrnamespace": 6,  # File namespace
        "gsrlimit": 15,
        "prop": "imageinfo",
        "iiprop": "url",
        "iiurlwidth": 1200,
    }
    response = requests.get(endpoint, params=params, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    data = response.json()
    pages = data.get("query", {}).get("pages", {})
    if not pages:
        return None

    topic_terms = set(re.findall(r"[a-z0-9]+", topic.lower()))
    best = None
    best_score = -1

    for page in pages.values():
        title = str(page.get("title", "")).lower()
        imageinfo = page.get("imageinfo", [])
        if not imageinfo:
            continue
        candidate_url = imageinfo[0].get("thumburl") or imageinfo[0].get("url")
        if not candidate_url:
            continue
        title_terms = set(re.findall(r"[a-z0-9]+", title))
        score = len(topic_terms.intersection(title_terms))
        if score > best_score:
            best_score = score
            best = candidate_url

    return best


def generate_image(topic):
    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "static" / "generated_images"
    output_dir.mkdir(parents=True, exist_ok=True)
    base_name = _safe_filename(topic)
    headers = {"User-Agent": "Mozilla/5.0"}

    prioritized_urls = []
    try:
        wiki_url = _wikimedia_image_url(topic)
        if wiki_url:
            prioritized_urls.append(wiki_url)
    except requests.RequestException:
        pass

    prioritized_urls.extend(_provider_urls(topic))

    for url in prioritized_urls:
        try:
            response = requests.get(url, timeout=20, headers=headers, allow_redirects=True)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
            if response.content and content_type.startswith("image/"):
                ext = _extension_from_content_type(content_type)
                file_path = output_dir / f"{base_name}{ext}"
                with open(file_path, "wb") as f:
                    f.write(response.content)
                return str(Path("static") / "generated_images" / file_path.name)
        except requests.RequestException:
            continue

    file_path = output_dir / f"{base_name}.png"
    with open(file_path, "wb") as f:
        f.write(_placeholder_png())

    return str(Path("static") / "generated_images" / file_path.name)
