"""Collect tokenization-related posts from Hugging Face blog RSS feed."""

import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from dataclasses import dataclass
from email.utils import parsedate_to_datetime


@dataclass
class BlogPost:
    title: str
    url: str
    published: str
    summary: str
    source: str = "huggingface_blog"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "authors": [],
            "abstract": self.summary,
            "url": self.url,
            "published": self.published,
            "source": self.source,
        }


def fetch_huggingface_blog(rss_url: str, keywords: list[str], lookback_days: int = 35) -> list[BlogPost]:
    """Fetch HuggingFace blog posts and filter for tokenization-related content."""
    posts = []
    cutoff = datetime.now() - timedelta(days=lookback_days)

    try:
        req = urllib.request.Request(rss_url, headers={"User-Agent": "TokenizationNewsletter/1.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read().decode("utf-8")

        root = ET.fromstring(data)

        # Handle both RSS 2.0 and Atom feeds
        items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")

        for item in items:
            # RSS 2.0 format
            title_el = item.find("title")
            link_el = item.find("link")
            desc_el = item.find("description")
            pubdate_el = item.find("pubDate")

            if title_el is None:
                continue

            title = title_el.text or ""
            link = link_el.text if link_el is not None else ""
            description = desc_el.text if desc_el is not None else ""

            # Parse date
            pub_date_str = ""
            if pubdate_el is not None and pubdate_el.text:
                try:
                    pub_date = parsedate_to_datetime(pubdate_el.text)
                    if pub_date.replace(tzinfo=None) < cutoff:
                        continue
                    pub_date_str = pub_date.strftime("%Y-%m-%d")
                except Exception:
                    pass

            # Check if tokenization-related
            text_to_search = (title + " " + description).lower()
            if any(kw.lower() in text_to_search for kw in keywords):
                posts.append(BlogPost(
                    title=title.strip(),
                    url=link.strip(),
                    published=pub_date_str,
                    summary=description[:500] if description else "",
                ))

    except Exception as e:
        print(f"Error fetching HuggingFace blog: {e}")

    return posts


if __name__ == "__main__":
    import yaml

    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    posts = fetch_huggingface_blog(
        rss_url=config["huggingface"]["blog_rss"],
        keywords=config["keywords"]["primary"],
        lookback_days=config["newsletter"]["lookback_days"],
    )
    print(f"Found {len(posts)} posts from HuggingFace blog")
    for p in posts:
        print(f"  - {p.title} ({p.published})")
