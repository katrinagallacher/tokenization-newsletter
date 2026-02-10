"""Collect tokenization-related posts from LessWrong and Alignment Forum via GraphQL API."""

import json
import urllib.request
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class Post:
    title: str
    authors: list[str]
    abstract: str
    url: str
    published: str
    source: str = "lesswrong"
    score: int = 0

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "url": self.url,
            "published": self.published,
            "source": self.source,
            "score": self.score,
        }


LESSWRONG_GRAPHQL = "https://www.lesswrong.com/graphql"
ALIGNMENT_FORUM_GRAPHQL = "https://www.alignmentforum.org/graphql"


def _query_forum(graphql_url: str, keywords: list[str], lookback_days: int = 35, limit: int = 50) -> list[dict]:
    """Query a LessWrong-style GraphQL API for recent posts."""
    cutoff = datetime.now() - timedelta(days=lookback_days)
    cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    # LW GraphQL doesn't support full-text search directly,
    # so we fetch recent posts and filter client-side
    query = """
    {
        posts(input: {
            terms: {
                view: "new"
                limit: %d
                after: "%s"
            }
        }) {
            results {
                _id
                title
                slug
                pageUrl
                postedAt
                baseScore
                voteCount
                commentCount
                user {
                    username
                    slug
                }
                plaintextExcerpt
            }
        }
    }
    """ % (limit, cutoff_str)

    body = json.dumps({"query": query}).encode("utf-8")

    req = urllib.request.Request(
        graphql_url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "TokenizationNewsletter/1.0",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

        results = data.get("data", {}).get("posts", {}).get("results", [])
        return results

    except Exception as e:
        print(f"Error querying {graphql_url}: {e}")
        return []


def _filter_by_keywords(posts: list[dict], keywords: list[str]) -> list[dict]:
    """Filter posts by tokenization-related keywords."""
    filtered = []
    for post in posts:
        text = ((post.get("title") or "") + " " + (post.get("plaintextExcerpt") or "")).lower()
        if any(kw.lower() in text for kw in keywords):
            filtered.append(post)
    return filtered


def _format_post(post: dict, source: str, base_url: str) -> Post:
    """Convert a GraphQL result into a Post object."""
    user = post.get("user") or {}
    author = user.get("username", "Unknown")

    page_url = post.get("pageUrl", "")
    if not page_url and post.get("slug"):
        page_url = f"{base_url}/posts/{post.get('_id', '')}/{post['slug']}"

    posted_at = post.get("postedAt", "")
    if posted_at:
        posted_at = posted_at[:10]

    return Post(
        title=post.get("title", "Untitled"),
        authors=[author],
        abstract=(post.get("plaintextExcerpt") or "")[:500],
        url=page_url,
        published=posted_at,
        source=source,
        score=post.get("baseScore", 0) or 0,
    )


def fetch_lesswrong(keywords: list[str], lookback_days: int = 35) -> list[Post]:
    """Fetch tokenization-related posts from LessWrong."""
    print("    Querying LessWrong...")
    raw = _query_forum(LESSWRONG_GRAPHQL, keywords, lookback_days, limit=100)
    filtered = _filter_by_keywords(raw, keywords)
    posts = [_format_post(p, "lesswrong", "https://www.lesswrong.com") for p in filtered]
    return posts


def fetch_alignment_forum(keywords: list[str], lookback_days: int = 35) -> list[Post]:
    """Fetch tokenization-related posts from EA Forum / Alignment Forum."""
    print("    Querying Alignment Forum...")
    raw = _query_forum(ALIGNMENT_FORUM_GRAPHQL, keywords, lookback_days, limit=100)
    filtered = _filter_by_keywords(raw, keywords)
    posts = [_format_post(p, "alignment_forum", "https://www.alignmentforum.org") for p in filtered]
    return posts


if __name__ == "__main__":
    import yaml

    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    keywords = config["keywords"]["primary"]

    lw_posts = fetch_lesswrong(keywords)
    print(f"Found {len(lw_posts)} posts from LessWrong")
    for p in lw_posts:
        print(f"  - [{p.score}] {p.title} ({p.published})")

    af_posts = fetch_alignment_forum(keywords)
    print(f"Found {len(af_posts)} posts from Alignment Forum")
    for p in af_posts:
        print(f"  - [{p.score}] {p.title} ({p.published})")
