#!/usr/bin/env python3
"""Tokenization Newsletter Pipeline.

Orchestrates: collect → filter → summarize → format → output

Usage:
    python -m src.pipeline                    # full run
    python -m src.pipeline --collect-only     # only collect & filter (no API calls)
    python -m src.pipeline --dry-run          # collect, filter, show results (no summarization)
    python -m src.pipeline --issue 3          # set issue number
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

from src.collectors.arxiv import search_arxiv
from src.collectors.semantic_scholar import search_semantic_scholar
from src.collectors.huggingface_blog import fetch_huggingface_blog
from src.collectors.google_scholar import fetch_google_scholar_alerts
from src.collectors.lesswrong import fetch_lesswrong, fetch_alignment_forum
from src.collectors.web_search import search_web_sources
from src.filter import filter_and_rank, filter_and_rank_with_rest, categorize_selections
from src.summarizer import batch_summarize, generate_editorial
from src.formatter import generate_markdown, generate_html


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def collect_all(config: dict) -> list[dict]:
    """Run all collectors and return combined raw papers."""
    all_papers = []
    lookback = config["newsletter"]["lookback_days"]
    primary_kw = config["keywords"]["primary"]

    # Arxiv
    print("📚 Collecting from arXiv...")
    arxiv_papers = search_arxiv(
        keywords=primary_kw,
        categories=config["arxiv"]["categories"],
        max_results=config["arxiv"]["max_results_per_query"],
        lookback_days=lookback,
    )
    print(f"   Found {len(arxiv_papers)} papers")
    all_papers.extend(p.to_dict() for p in arxiv_papers)

    # Semantic Scholar
    print("🔬 Collecting from Semantic Scholar...")
    s2_papers = search_semantic_scholar(
        keywords=primary_kw,
        max_results=config["semantic_scholar"]["max_results_per_query"],
        lookback_days=lookback,
    )
    print(f"   Found {len(s2_papers)} papers")
    all_papers.extend(p.to_dict() for p in s2_papers)

    # Hugging Face blog
    print("🤗 Collecting from Hugging Face blog...")
    hf_posts = fetch_huggingface_blog(
        rss_url=config["huggingface"]["blog_rss"],
        keywords=primary_kw,
        lookback_days=lookback,
    )
    print(f"   Found {len(hf_posts)} posts")
    all_papers.extend(p.to_dict() for p in hf_posts)

    # Google Scholar alerts
    feeds = config.get("google_scholar", {}).get("alert_feeds", [])
    if feeds:
        print("🎓 Collecting from Google Scholar alerts...")
        gs_papers = fetch_google_scholar_alerts(feeds, lookback_days=lookback)
        print(f"   Found {len(gs_papers)} papers")
        all_papers.extend(p.to_dict() for p in gs_papers)
    else:
        print("⏭️  No Google Scholar alert feeds configured, skipping")

    # LessWrong
    print("📝 Collecting from LessWrong...")
    lw_posts = fetch_lesswrong(keywords=primary_kw, lookback_days=lookback)
    print(f"   Found {len(lw_posts)} posts")
    all_papers.extend(p.to_dict() for p in lw_posts)

    # Alignment Forum
    print("🔍 Collecting from Alignment Forum...")
    af_posts = fetch_alignment_forum(keywords=primary_kw, lookback_days=lookback)
    print(f"   Found {len(af_posts)} posts")
    all_papers.extend(p.to_dict() for p in af_posts)

    # Web search (Medium, Substack, Emergent Mind, blogs, Twitter)
    # Uses Haiku model (cheaper, separate rate limit from Sonnet)
    if os.environ.get("ANTHROPIC_API_KEY"):
        print("🌐 Collecting from web (Medium, Substack, blogs, Emergent Mind)...")
        web_model = config.get("claude", {}).get("web_search_model", "claude-haiku-4-5-20251001")
        web_posts = search_web_sources(
            keywords=primary_kw,
            lookback_days=lookback,
            model=web_model,
        )
        print(f"   Found {len(web_posts)} posts")
        all_papers.extend(p.to_dict() for p in web_posts)
    else:
        print("⏭️  No ANTHROPIC_API_KEY set, skipping web search collector")

    return all_papers


def run_pipeline(config_path: str = "config.yaml", issue_number: int = 1,
                 collect_only: bool = False, dry_run: bool = False) -> dict:
    """Run the full newsletter pipeline."""
    config = load_config(config_path)

    print(f"\n{'='*60}")
    print(f"  Tokenization Digest — Issue #{issue_number}")
    print(f"  {datetime.now().strftime('%B %Y')}")
    print(f"{'='*60}\n")

    # Step 1: Collect
    print("STEP 1: Collecting papers...")
    all_papers = collect_all(config)
    print(f"\n📊 Total collected: {len(all_papers)} items\n")

    # Step 2: Filter & rank
    print("STEP 2: Filtering and ranking...")
    filtered, rest = filter_and_rank_with_rest(
        papers=all_papers,
        primary_keywords=config["keywords"]["primary"],
        secondary_keywords=config["keywords"]["secondary"],
        max_items=20,  # get more candidates for categorization
    )

    # Categorize into sections
    sections = categorize_selections(filtered)
    text_papers = sections["text_papers"]
    text_blogs = sections["text_blogs"]
    other_papers = sections["other_papers"]

    # All selected items (for summarization)
    selected = text_papers + text_blogs + other_papers
    selected_titles = {p.get("title") for p in selected}

    # Rest = everything not selected
    rest = [p for p in filtered + rest if p.get("title") not in selected_titles]

    print(f"📊 Text papers: {len(text_papers)} | Text blogs: {len(text_blogs)} | Other: {len(other_papers)} | Also found: {len(rest)} more\n")

    print("  📝 Text Processing / Linguistics:")
    for p in text_papers:
        print(f"    [{p.get('relevance_score', 0):.2f}] {p['title']}")
    for p in text_blogs:
        print(f"    [{p.get('relevance_score', 0):.2f}] [blog] {p['title']}")
    print("  🔊 Audio / Video / Other:")
    for p in other_papers:
        print(f"    [{p.get('relevance_score', 0):.2f}] {p['title']}")
    print()

    if collect_only:
        output_path = Path("output") / f"collected_{datetime.now().strftime('%Y%m%d')}.json"
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"raw": all_papers, "filtered": filtered}, f, indent=2)
        print(f"💾 Saved collected data to {output_path}")
        return {"papers": filtered}

    if dry_run:
        print("🏁 Dry run complete. Papers above would be included in the newsletter.")
        return {"papers": filtered}

    # Wait for rate limit window to reset after web search
    print("⏳ Waiting 60s for rate limit buffer...")
    time.sleep(60)

    # Step 3: Summarize selected items with Claude
    print("STEP 3: Generating summaries with Claude...")
    max_tokens = config["claude"]["max_tokens_summary"]
    selected = batch_summarize(selected, max_tokens_per_summary=max_tokens)
    print(f"✅ Summarized {len(selected)} items\n")

    # Re-split after summarization (summaries are now attached)
    n_tp = len(sections["text_papers"])
    n_tb = len(sections["text_blogs"])
    text_papers = selected[:n_tp]
    text_blogs = selected[n_tp:n_tp + n_tb]
    other_papers = selected[n_tp + n_tb:]

    # Step 4: Format output
    print("STEP 4: Formatting newsletter...")
    date_str = datetime.now().strftime("%B %Y")

    md_output = generate_markdown(text_papers=text_papers, text_blogs=text_blogs,
                                  other_papers=other_papers, rest=rest,
                                  issue_number=issue_number, date=date_str)
    html_output = generate_html(text_papers=text_papers, text_blogs=text_blogs,
                                other_papers=other_papers, rest=rest,
                                issue_number=issue_number, date=date_str)

    # Save outputs
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    date_slug = datetime.now().strftime("%Y%m")
    md_path = output_dir / f"issue_{issue_number}_{date_slug}.md"
    html_path = output_dir / f"issue_{issue_number}_{date_slug}.html"
    json_path = output_dir / f"issue_{issue_number}_{date_slug}_data.json"

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_output)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_output)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "issue": issue_number,
            "date": date_str,
            "text_papers": text_papers,
            "text_blogs": text_blogs,
            "other_papers": other_papers,
            "rest": [{"title": p.get("title"), "url": p.get("url")} for p in rest],
        }, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  ✅ Newsletter generated!")
    print(f"  📝 Markdown: {md_path}")
    print(f"  🌐 HTML:     {html_path}")
    print(f"  💾 Data:     {json_path}")
    print(f"  ✏️  Now open the HTML, add your Human's Pick, and publish!")
    print(f"{'='*60}\n")

    return {
        "papers": selected,
        "md_path": str(md_path),
        "html_path": str(html_path),
    }


def main():
    parser = argparse.ArgumentParser(description="Tokenization Newsletter Pipeline")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--issue", type=int, default=1, help="Issue number")
    parser.add_argument("--collect-only", action="store_true", help="Only collect and filter, no API calls")
    parser.add_argument("--dry-run", action="store_true", help="Collect and filter, show results, no summarization")
    args = parser.parse_args()

    run_pipeline(
        config_path=args.config,
        issue_number=args.issue,
        collect_only=args.collect_only,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
