"""Collect tokenization-related papers from Semantic Scholar API."""

import urllib.request
import urllib.parse
import json
import time
import random
import os
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class Paper:
    title: str
    authors: list[str]
    abstract: str
    url: str
    published: str
    source: str = "semantic_scholar"
    paper_id: str = ""
    citation_count: int = 0
    venue: str = ""

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "url": self.url,
            "published": self.published,
            "source": self.source,
            "paper_id": self.paper_id,
            "citation_count": self.citation_count,
            "venue": self.venue,
        }


S2_API = "https://api.semanticscholar.org/graph/v1/paper/search"
USER_AGENT = "TokenizationDigest/1.0 (newsletter pipeline; https://github.com)"


def _get_s2_headers() -> dict:
    """Build request headers, including API key if available."""
    headers = {"User-Agent": USER_AGENT}
    api_key = os.environ.get("S2_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key
    return headers


def _fetch_with_retry(url: str, headers: dict = None, max_retries: int = 5, base_delay: float = 30.0) -> str:
    """Fetch a URL with exponential backoff on 429s and timeouts."""
    if headers is None:
        headers = {}
    headers.setdefault("User-Agent", USER_AGENT)

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < max_retries - 1:
                retry_after = e.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    delay = int(retry_after) + random.uniform(1, 5)
                else:
                    delay = base_delay * (2 ** attempt) + random.uniform(1, 10)
                print(f"  HTTP {e.code}, retrying in {delay:.0f}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                raise
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(1, 10)
                print(f"  Timeout/error, retrying in {delay:.0f}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                raise


def search_semantic_scholar(keywords: list[str], max_results: int = 30,
                            start_date: str = "", end_date: str = "",
                            lookback_days: int = 35) -> list[Paper]:
    """Search Semantic Scholar for tokenization-related papers.

    Args:
        start_date: ISO date string (e.g. "2026-04-01").
        end_date:   ISO date string (e.g. "2026-04-30").
        lookback_days: Fallback if start_date/end_date are not provided.
    """
    papers = []
    headers = _get_s2_headers()
    has_api_key = "x-api-key" in headers

    if has_api_key:
        print("  Using S2 API key (authenticated)")
    else:
        print("  No S2_API_KEY set — using unauthenticated access (shared rate limit)")

    # Build date range for S2 API
    if start_date and end_date:
        date_range = f"{start_date}:{end_date}"
    else:
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=lookback_days)
        date_range = f"{cutoff.strftime('%Y-%m-%d')}:"

    for i, keyword in enumerate(keywords):
        params = {
            "query": keyword,
            "limit": min(max_results, 100),
            "fields": "title,authors,abstract,url,publicationDate,citationCount,venue,externalIds",
            "publicationDateOrYear": date_range,
            "fieldsOfStudy": "Computer Science",
        }

        url = f"{S2_API}?{urllib.parse.urlencode(params)}"

        try:
            data = json.loads(_fetch_with_retry(url, headers=headers))

            for item in data.get("data", []):
                if not item.get("title") or not item.get("abstract"):
                    continue

                authors = [a.get("name", "") for a in item.get("authors", [])]
                pub_date = item.get("publicationDate", "")

                external = item.get("externalIds", {}) or {}
                if external.get("ArXiv"):
                    paper_url = f"https://arxiv.org/abs/{external['ArXiv']}"
                else:
                    paper_url = item.get("url", "")

                paper = Paper(
                    title=item["title"],
                    authors=authors,
                    abstract=item.get("abstract", ""),
                    url=paper_url,
                    published=pub_date or "",
                    paper_id=item.get("paperId", ""),
                    citation_count=item.get("citationCount", 0) or 0,
                    venue=item.get("venue", "") or "",
                )
                papers.append(paper)

            print(f"  Keyword '{keyword}': {len(data.get('data', []))} results")

        except Exception as e:
            print(f"Error searching Semantic Scholar for '{keyword}': {e}")

        if i < len(keywords) - 1:
            delay = 2 + random.uniform(0, 1) if has_api_key else 5 + random.uniform(0, 3)
            time.sleep(delay)

    # Deduplicate by title
    seen_titles = set()
    unique = []
    for p in papers:
        normalized = p.title.lower().strip()
        if normalized not in seen_titles:
            seen_titles.add(normalized)
            unique.append(p)

    return unique


if __name__ == "__main__":
    import yaml

    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    papers = search_semantic_scholar(
        keywords=config["keywords"]["primary"],
        max_results=config["semantic_scholar"]["max_results_per_query"],
    )
    print(f"Found {len(papers)} papers from Semantic Scholar")
    for p in papers[:5]:
        print(f"  - {p.title} ({p.published}) [citations: {p.citation_count}]")

