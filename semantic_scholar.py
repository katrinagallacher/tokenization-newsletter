"""Collect tokenization-related papers from Semantic Scholar API."""

import urllib.request
import urllib.parse
import json
from datetime import datetime, timedelta
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


def search_semantic_scholar(keywords: list[str], max_results: int = 30, lookback_days: int = 35) -> list[Paper]:
    """Search Semantic Scholar for tokenization-related papers."""
    papers = []
    cutoff = datetime.now() - timedelta(days=lookback_days)
    cutoff_str = cutoff.strftime("%Y-%m-%d")

    for keyword in keywords:
        params = {
            "query": keyword,
            "limit": min(max_results, 100),
            "fields": "title,authors,abstract,url,publicationDate,citationCount,venue,externalIds",
            "publicationDateOrYear": f"{cutoff_str}:",
            "fieldsOfStudy": "Computer Science",
        }

        url = f"{S2_API}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TokenizationNewsletter/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))

            for item in data.get("data", []):
                if not item.get("title") or not item.get("abstract"):
                    continue

                authors = [a.get("name", "") for a in item.get("authors", [])]
                pub_date = item.get("publicationDate", "")

                # Get arxiv URL if available, otherwise S2 URL
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

        except Exception as e:
            print(f"Error searching Semantic Scholar for '{keyword}': {e}")

    # Deduplicate by title similarity (simple lowercase match)
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
        lookback_days=config["newsletter"]["lookback_days"],
    )
    print(f"Found {len(papers)} papers from Semantic Scholar")
    for p in papers[:5]:
        print(f"  - {p.title} ({p.published}) [citations: {p.citation_count}]")
