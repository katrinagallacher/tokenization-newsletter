"""Collect papers from Google Scholar alert RSS feeds.

Google Scholar alerts can be set up manually:
1. Go to scholar.google.com
2. Search for your topic (e.g., "tokenization language model")
3. Click "Create alert" (envelope icon)
4. Get the RSS feed URL from the alert settings

The RSS feed URLs should be added to config.yaml under google_scholar.alert_feeds
"""

import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
import html
import re


@dataclass
class Paper:
    title: str
    authors: list[str]
    abstract: str
    url: str
    published: str
    source: str = "google_scholar"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "url": self.url,
            "published": self.published,
            "source": self.source,
        }


def clean_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def fetch_google_scholar_alerts(feed_urls: list[str], lookback_days: int = 35) -> list[Paper]:
    """Fetch papers from Google Scholar alert RSS feeds."""
    papers = []
    cutoff = datetime.now() - timedelta(days=lookback_days)

    for feed_url in feed_urls:
        if not feed_url:
            continue

        try:
            req = urllib.request.Request(feed_url, headers={"User-Agent": "TokenizationNewsletter/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read().decode("utf-8")

            root = ET.fromstring(data)
            items = root.findall(".//item") or root.findall(".//entry")

            for item in items:
                title_el = item.find("title")
                link_el = item.find("link")
                desc_el = item.find("description") or item.find("summary")
                pubdate_el = item.find("pubDate") or item.find("updated")

                if title_el is None:
                    continue

                title = clean_html(title_el.text or "")
                description = clean_html(desc_el.text or "") if desc_el is not None else ""

                # Get link
                link = ""
                if link_el is not None:
                    link = link_el.text or link_el.get("href", "")

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

                # Try to extract authors from description
                authors = []
                author_match = re.search(r"^(.*?)\s*[-–—]\s", description)
                if author_match:
                    authors = [a.strip() for a in author_match.group(1).split(",")]

                papers.append(Paper(
                    title=title,
                    authors=authors,
                    abstract=description[:500],
                    url=link,
                    published=pub_date_str,
                ))

        except Exception as e:
            print(f"Error fetching Google Scholar feed: {e}")

    return papers


if __name__ == "__main__":
    import yaml

    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    feeds = config.get("google_scholar", {}).get("alert_feeds", [])
    if not feeds:
        print("No Google Scholar alert feeds configured.")
        print("Set up alerts at scholar.google.com and add RSS feed URLs to config.yaml")
    else:
        papers = fetch_google_scholar_alerts(feeds, lookback_days=config["newsletter"]["lookback_days"])
        print(f"Found {len(papers)} papers from Google Scholar alerts")
        for p in papers:
            print(f"  - {p.title} ({p.published})")
