"""Generate summaries and editorial using Claude API."""

import json
import os
import urllib.request


ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


def call_claude(prompt: str, system: str = "", max_tokens: int = 1000, model: str = "claude-sonnet-4-20250514") -> str:
    """Call Claude API and return the response text."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    messages = [{"role": "user", "content": prompt}]

    body = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if system:
        body["system"] = system

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
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["content"][0]["text"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"Claude API error {e.code}: {error_body}")


def summarize_paper(paper: dict, max_tokens: int = 150) -> str:
    """Generate a concise summary and commentary for a paper."""
    system = """You are writing for a monthly tokenization research newsletter.
Write a single flowing paragraph summarizing the paper: what it does, key findings, and why it matters.
No bold text, no labels, no bullet points.
Just smooth, readable, technically precise prose. Keep it under 80 words."""

    prompt = f"""Summarize this paper for the newsletter:

Title: {paper.get('title', 'Unknown')}
Authors: {', '.join(paper.get('authors', ['Unknown']))}
Abstract: {paper.get('abstract', 'No abstract available.')}

Write a brief, informative summary with commentary."""

    return call_claude(prompt, system=system, max_tokens=max_tokens)


def generate_editorial(papers: list[dict], max_tokens: int = 300) -> str:
    """Generate an editorial connecting the month's papers into a narrative."""
    system = """You are the editor of "Tokenization Digest," a monthly newsletter about LLM tokenization research.
Write a brief editorial (100-200 words) that:
1. Opens with a compelling observation about this month's collection
2. Identifies themes or trends across the papers
3. Highlights 1-2 papers that are particularly noteworthy and why
4. Ends with a forward-looking thought about where tokenization research is heading

Tone: knowledgeable, accessible, slightly opinionated. You have genuine expertise.
Do NOT use bullet points. Write in flowing paragraphs.
Do NOT be generic — make specific connections between papers."""

    paper_summaries = []
    for i, p in enumerate(papers, 1):
        paper_summaries.append(
            f"{i}. \"{p.get('title', 'Unknown')}\" by {', '.join(p.get('authors', ['Unknown'])[:3])}\n"
            f"   Abstract: {p.get('abstract', '')[:300]}..."
        )

    prompt = f"""Write the editorial for this month's Tokenization Digest.

This month's papers:
{chr(10).join(paper_summaries)}

Write the editorial."""

    return call_claude(prompt, system=system, max_tokens=max_tokens)


def batch_summarize(papers: list[dict], max_tokens_per_summary: int = 150) -> list[dict]:
    """Summarize all papers, adding 'summary' field to each."""
    for paper in papers:
        try:
            paper["summary"] = summarize_paper(paper, max_tokens=max_tokens_per_summary)
        except Exception as e:
            print(f"Error summarizing '{paper.get('title', '?')}': {e}")
            paper["summary"] = f"*Summary unavailable.* Read the full paper: {paper.get('url', '')}"
    return papers


if __name__ == "__main__":
    # Test with a fake paper
    test_paper = {
        "title": "Tokenization Is More Than Compression",
        "authors": ["John Doe", "Jane Smith"],
        "abstract": "We demonstrate that tokenization choices significantly impact language model performance beyond simple compression efficiency. Through controlled experiments across 12 languages, we show that tokenization artifacts in morphologically rich languages lead to systematic degradation in downstream task performance.",
        "url": "https://arxiv.org/abs/2024.12345",
    }

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        summary = summarize_paper(test_paper)
        print("Summary:", summary)
    else:
        print("Set ANTHROPIC_API_KEY to test summarization")
