"""Filter and deduplicate collected papers/posts.

Handles:
- Cross-source deduplication (same paper from arxiv + semantic scholar)
- Relevance scoring based on keyword matches
- Ranking by relevance and recency
"""

import re
from difflib import SequenceMatcher


def normalize_title(title: str) -> str:
    """Normalize title for comparison."""
    title = title.lower().strip()
    title = re.sub(r"[^a-z0-9\s]", "", title)
    title = re.sub(r"\s+", " ", title)
    return title


def titles_match(title1: str, title2: str, threshold: float = 0.85) -> bool:
    """Check if two titles refer to the same paper."""
    n1 = normalize_title(title1)
    n2 = normalize_title(title2)
    return SequenceMatcher(None, n1, n2).ratio() >= threshold


def compute_relevance_score(paper: dict, primary_keywords: list[str], secondary_keywords: list[str]) -> float:
    """Score a paper's relevance to tokenization research.
    
    Returns a score between 0 and 1.
    """
    text = (paper.get("title", "") + " " + paper.get("abstract", "")).lower()
    
    score = 0.0
    
    # Primary keyword matches (high weight)
    primary_matches = sum(1 for kw in primary_keywords if kw.lower() in text)
    score += min(primary_matches * 0.2, 0.6)  # cap at 0.6
    
    # Title matches are extra valuable
    title_lower = paper.get("title", "").lower()
    title_primary = sum(1 for kw in primary_keywords if kw.lower() in title_lower)
    score += min(title_primary * 0.15, 0.3)
    
    # Secondary keyword matches (lower weight)
    secondary_matches = sum(1 for kw in secondary_keywords if kw.lower() in text)
    score += min(secondary_matches * 0.05, 0.2)
    
    # Citation boost (for Semantic Scholar results)
    citations = paper.get("citation_count", 0)
    if citations > 0:
        score += min(citations * 0.01, 0.1)
    
    return min(score, 1.0)


def deduplicate_papers(papers: list[dict]) -> list[dict]:
    """Remove duplicate papers across sources, keeping the richest version."""
    unique = []
    
    for paper in papers:
        is_dup = False
        for i, existing in enumerate(unique):
            if titles_match(paper.get("title", ""), existing.get("title", "")):
                # Keep the version with more information
                paper_richness = len(paper.get("abstract", "")) + len(paper.get("authors", []))
                existing_richness = len(existing.get("abstract", "")) + len(existing.get("authors", []))
                
                if paper_richness > existing_richness:
                    # Merge sources info
                    paper["also_found_in"] = existing.get("source", "")
                    unique[i] = paper
                else:
                    existing["also_found_in"] = paper.get("source", "")
                
                is_dup = True
                break
        
        if not is_dup:
            unique.append(paper)
    
    return unique


def filter_and_rank(
    papers: list[dict],
    primary_keywords: list[str],
    secondary_keywords: list[str],
    max_items: int = 10,
    min_relevance: float = 0.15,
) -> list[dict]:
    """Full pipeline: deduplicate, score, filter, and rank papers."""
    
    # Deduplicate
    papers = deduplicate_papers(papers)
    
    # Score relevance
    for paper in papers:
        paper["relevance_score"] = compute_relevance_score(paper, primary_keywords, secondary_keywords)
    
    # Filter by minimum relevance
    papers = [p for p in papers if p["relevance_score"] >= min_relevance]
    
    # Sort by relevance (primary) and date (secondary)
    papers.sort(key=lambda p: (p["relevance_score"], p.get("published", "")), reverse=True)
    
    # Return top N
    return papers[:max_items]


def filter_and_rank_with_rest(
    papers: list[dict],
    primary_keywords: list[str],
    secondary_keywords: list[str],
    max_items: int = 10,
    min_relevance: float = 0.15,
) -> tuple[list[dict], list[dict]]:
    """Same as filter_and_rank but also returns remaining papers.
    
    Returns:
        (top_papers, rest_papers)
    """
    papers = deduplicate_papers(papers)

    for paper in papers:
        paper["relevance_score"] = compute_relevance_score(paper, primary_keywords, secondary_keywords)

    papers = [p for p in papers if p["relevance_score"] >= min_relevance]

    # Sort by relevance, but reserve slots for non-academic sources
    academic = [p for p in papers if p.get("source") in ("arxiv", "semantic_scholar", "google_scholar")]
    non_academic = [p for p in papers if p.get("source") not in ("arxiv", "semantic_scholar", "google_scholar")]

    academic.sort(key=lambda p: (p["relevance_score"], p.get("published", "")), reverse=True)
    non_academic.sort(key=lambda p: (p["relevance_score"], p.get("published", "")), reverse=True)

    reserved = non_academic[:2]
    remaining = academic + non_academic[2:]
    remaining.sort(key=lambda p: (p["relevance_score"], p.get("published", "")), reverse=True)

    all_ranked = reserved + remaining
    top = all_ranked[:max_items]
    rest = all_ranked[max_items:]

    return top, rest


if __name__ == "__main__":
    # Quick test
    test_papers = [
        {
            "title": "Tokenization Is More Than Compression",
            "abstract": "We study the effect of tokenization on language model performance...",
            "source": "arxiv",
            "published": "2025-01-15",
        },
        {
            "title": "A Survey of Deep Learning Techniques",
            "abstract": "This paper surveys various deep learning methods...",
            "source": "semantic_scholar",
            "published": "2025-01-10",
        },
        {
            "title": "Tokenization is More Than Compression",  # duplicate
            "abstract": "We study the effect of tokenization on language model performance across languages.",
            "source": "semantic_scholar",
            "published": "2025-01-15",
        },
    ]
    
    primary = ["tokenization", "tokenizer", "BPE"]
    secondary = ["language model", "LLM"]
    
    result = filter_and_rank(test_papers, primary, secondary)
    print(f"Filtered to {len(result)} papers:")
    for p in result:
        print(f"  [{p['relevance_score']:.2f}] {p['title']}")
