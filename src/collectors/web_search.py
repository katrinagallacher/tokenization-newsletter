"""Collect tokenization-related posts from the broader web.

Uses Claude API with web search to find posts on:
- Medium
- Substack
- Emergent Mind
- Personal blogs
- Twitter/X threads

This is a "smart" collector that uses an LLM to search and extract relevant items,
since these platforms don't have convenient structured APIs for our use case.
"""

import json
import os
import urllib.request
from datetime import datetime, timedelta
from dataclasses import dataclass


ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


@dataclass
class WebPost:
    title: str
    authors: list[str]
    abstract: str
    url: str
    published: str
    source: str = "web"
    platform: str = ""

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "url": self.url,
            "published": self.published,
            "source": self.source,
            "platform": self.platform,
        }


def _call_claude_with_search(prompt: str, system: str = "", model: str = "claude-sonnet-4-20250514") -> str:
    """Call Claude API with web search tool enabled."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    body = {
        "model": model,
        "max_tokens": 4000,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
        "tools": [
            {
                "type": "web_search_20250305",
                "name": "web_search",
            }
        ],
    }

    data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
            # Extract text from potentially mixed content blocks
            texts = []
            for block in result.get("content", []):
                if block.get("type") == "text":
                    texts.append(block["text"])
            return "\n".join(texts)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"Claude API error {e.code}: {error_body}")


def search_web_sources(keywords: list[str], lookback_days: int = 35, model: str = "claude-sonnet-4-20250514") -> list[WebPost]:
    """Use Claude with web search to find tokenization posts across the web."""
    cutoff_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")

    keyword_str = ", ".join(keywords[:5])

    system = """You are a research assistant collecting recent posts about LLM tokenization.
You must search the web and return results as a JSON array.
Return ONLY valid JSON, no markdown backticks, no preamble, no explanation.
If you find no results, return an empty array: []"""

    prompt = f"""Search for recent blog posts, articles, and discussions about LLM tokenization 
published between {cutoff_date} and {today}.

Search these platforms specifically:
1. Medium articles about tokenization, BPE, tokenizers in LLMs
2. Substack posts about tokenization research
3. emergentmind.com for trending tokenization papers
4. Twitter/X threads about tokenization research
5. Any other notable blog posts about tokenization

Keywords to search for: {keyword_str}

For each result found, extract:
- title: the post/article title
- author: author name
- url: the URL
- summary: 1-2 sentence description
- published: publication date (YYYY-MM-DD format, approximate if needed)
- platform: which platform (medium, substack, emergentmind, twitter, blog)

Return results as a JSON array of objects with those fields.
Return ONLY the JSON array, nothing else. No markdown formatting.
Example: [{{"title": "...", "author": "...", "url": "...", "summary": "...", "published": "...", "platform": "..."}}]"""

    import time
    response_text = ""
    for attempt in range(3):
        try:
            if attempt > 0:
                print(f"    Retry {attempt}/2, waiting 30s...")
                time.sleep(30)
            response_text = _call_claude_with_search(prompt, system=system, model=model)
            break
        except RuntimeError as e:
            if "rate_limit" in str(e) and attempt < 2:
                continue
            else:
                print(f"Error in web search collector: {e}")
                return []
        except Exception as e:
            print(f"Error in web search collector: {e}")
            return []

    try:
        # Clean up response - remove any markdown formatting
        response_text = response_text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[-1]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

        # Parse JSON
        items = json.loads(response_text)

        posts = []
        for item in items:
            if not item.get("title") or not item.get("url"):
                continue
            post = WebPost(
                title=item.get("title", "Untitled"),
                authors=[item.get("author", "Unknown")],
                abstract=item.get("summary", "")[:500],
                url=item.get("url", ""),
                published=item.get("published", ""),
                source="web",
                platform=item.get("platform", "blog"),
            )
            posts.append(post)

        return posts

    except json.JSONDecodeError as e:
        print(f"Error parsing web search results as JSON: {e}")
        print(f"Raw response: {response_text[:500]}")
        return []


if __name__ == "__main__":
    import yaml

    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY to test web search collector")
    else:
        posts = search_web_sources(
            keywords=config["keywords"]["primary"],
            lookback_days=config["newsletter"]["lookback_days"],
        )
        print(f"Found {len(posts)} posts from web search")
        for p in posts:
            print(f"  - [{p.platform}] {p.title} ({p.published})")
            print(f"    {p.url}")
