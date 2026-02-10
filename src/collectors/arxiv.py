"""Collect tokenization-related papers from arxiv API."""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class Paper:
    title: str
    authors: list[str]
    abstract: str
    url: str
    published: str
    source: str = "arxiv"
    arxiv_id: str = ""
    categories: list[str] = None

    def __post_init__(self):
        if self.categories is None:
            self.categories = []

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "url": self.url,
            "published": self.published,
            "source": self.source,
            "arxiv_id": self.arxiv_id,
            "categories": self.categories,
        }


ARXIV_API = "http://export.arxiv.org/api/query"
ARXIV_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def search_arxiv(keywords: list[str], categories: list[str], max_results: int = 50, lookback_days: int = 35) -> list[Paper]:
    """Search arxiv for papers matching keywords in given categories."""
    papers = []

    for keyword in keywords:
        # Build query: keyword in title or abstract, within categories
        cat_query = " OR ".join(f"cat:{cat}" for cat in categories)
        query = f"(ti:\"{keyword}\" OR abs:\"{keyword}\") AND ({cat_query})"

        params = {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"

        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                data = response.read().decode("utf-8")

            root = ET.fromstring(data)
            cutoff = datetime.now() - timedelta(days=lookback_days)

            for entry in root.findall("atom:entry", ARXIV_NS):
                published_str = entry.find("atom:published", ARXIV_NS).text
                published_date = datetime.fromisoformat(published_str.replace("Z", "+00:00"))

                if published_date.replace(tzinfo=None) < cutoff:
                    continue

                title = entry.find("atom:title", ARXIV_NS).text.strip().replace("\n", " ")
                abstract = entry.find("atom:summary", ARXIV_NS).text.strip().replace("\n", " ")

                authors = []
                for author in entry.findall("atom:author", ARXIV_NS):
                    name = author.find("atom:name", ARXIV_NS).text
                    authors.append(name)

                link = entry.find("atom:id", ARXIV_NS).text
                arxiv_id = link.split("/abs/")[-1]

                cats = []
                for cat in entry.findall("arxiv:primary_category", ARXIV_NS):
                    cats.append(cat.get("term"))
                for cat in entry.findall("atom:category", ARXIV_NS):
                    term = cat.get("term")
                    if term not in cats:
                        cats.append(term)

                paper = Paper(
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    url=f"https://arxiv.org/abs/{arxiv_id}",
                    published=published_str[:10],
                    arxiv_id=arxiv_id,
                    categories=cats,
                )
                papers.append(paper)

        except Exception as e:
            print(f"Error searching arxiv for '{keyword}': {e}")

    # Deduplicate by arxiv_id
    seen = set()
    unique = []
    for p in papers:
        if p.arxiv_id not in seen:
            seen.add(p.arxiv_id)
            unique.append(p)

    return unique


if __name__ == "__main__":
    import yaml

    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    papers = search_arxiv(
        keywords=config["keywords"]["primary"],
        categories=config["arxiv"]["categories"],
        max_results=config["arxiv"]["max_results_per_query"],
        lookback_days=config["newsletter"]["lookback_days"],
    )
    print(f"Found {len(papers)} papers from arxiv")
    for p in papers[:5]:
        print(f"  - {p.title} ({p.published})")
