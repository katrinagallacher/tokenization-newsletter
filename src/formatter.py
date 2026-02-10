"""Format the newsletter as Markdown and HTML for Substack."""

from datetime import datetime


def format_authors(authors: list[str], max_show: int = 3) -> str:
    """Format author list, truncating if too long."""
    if not authors:
        return "Unknown authors"
    if len(authors) <= max_show:
        return ", ".join(authors)
    return ", ".join(authors[:max_show]) + f" et al. ({len(authors)} authors)"


def generate_markdown(papers: list[dict], editorial: str, issue_number: int = 1, date: str = "") -> str:
    """Generate the full newsletter as Markdown."""
    if not date:
        date = datetime.now().strftime("%B %Y")

    lines = []

    # Header
    lines.append(f"# Tokenization Digest — Issue #{issue_number}")
    lines.append(f"*{date}*")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Editorial
    lines.append("## Editor's Note")
    lines.append("")
    lines.append(editorial)
    lines.append("")
    lines.append("---")
    lines.append("")

    # Papers
    lines.append("## This Month's Papers & Posts")
    lines.append("")

    for i, paper in enumerate(papers, 1):
        title = paper.get("title", "Untitled")
        authors = format_authors(paper.get("authors", []))
        url = paper.get("url", "")
        published = paper.get("published", "")
        source = paper.get("source", "")
        summary = paper.get("summary", "")
        venue = paper.get("venue", "")

        lines.append(f"### {i}. {title}")
        lines.append("")

        # Metadata line
        meta_parts = []
        if authors != "Unknown authors":
            meta_parts.append(f"**Authors:** {authors}")
        if venue:
            meta_parts.append(f"**Venue:** {venue}")
        if published:
            meta_parts.append(f"**Published:** {published}")
        if source:
            source_label = {
                "arxiv": "arXiv",
                "semantic_scholar": "Semantic Scholar",
                "huggingface_blog": "Hugging Face Blog",
                "google_scholar": "Google Scholar",
                "lesswrong": "LessWrong",
                "alignment_forum": "Alignment Forum",
                "web": "Web",
            }.get(source, source)
            meta_parts.append(f"**Found via:** {source_label}")

        lines.append(" | ".join(meta_parts))
        lines.append("")

        if url:
            lines.append(f"🔗 [{url}]({url})")
            lines.append("")

        if summary:
            lines.append(summary)
            lines.append("")

        lines.append("---")
        lines.append("")

    # Footer
    lines.append("## About")
    lines.append("")
    lines.append("**Tokenization Digest** is a monthly newsletter tracking research and developments in LLM tokenization. "
                 "Whether you're a seasoned researcher or just getting started, we aim to keep you informed about "
                 "what's happening in this foundational area of language modeling.")
    lines.append("")
    lines.append("*Have a paper, post, or project related to tokenization? Reply to this newsletter or reach out!*")
    lines.append("")
    lines.append("---")
    lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d')}*")

    return "\n".join(lines)


def generate_html(papers: list[dict], editorial: str, issue_number: int = 1, date: str = "") -> str:
    """Generate newsletter as HTML (Substack-compatible)."""
    if not date:
        date = datetime.now().strftime("%B %Y")

    # Simple, clean HTML that works well in Substack
    html_parts = []

    html_parts.append(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Tokenization Digest — Issue #{issue_number}</title>
<style>
body {{ font-family: Georgia, serif; max-width: 680px; margin: 0 auto; padding: 20px; color: #333; line-height: 1.6; }}
h1 {{ font-size: 28px; margin-bottom: 5px; }}
h2 {{ font-size: 22px; color: #555; border-bottom: 1px solid #ddd; padding-bottom: 8px; }}
h3 {{ font-size: 18px; margin-bottom: 5px; }}
.subtitle {{ color: #888; font-style: italic; margin-bottom: 30px; }}
.meta {{ font-size: 14px; color: #666; margin-bottom: 10px; }}
.summary {{ margin: 15px 0; }}
.paper-link {{ font-size: 14px; }}
hr {{ border: none; border-top: 1px solid #eee; margin: 25px 0; }}
.editorial {{ font-size: 16px; line-height: 1.7; }}
.footer {{ font-size: 14px; color: #888; margin-top: 40px; }}
</style>
</head>
<body>
""")

    html_parts.append(f'<h1>Tokenization Digest — Issue #{issue_number}</h1>')
    html_parts.append(f'<p class="subtitle">{date}</p>')
    html_parts.append('<hr>')

    # Editorial
    html_parts.append('<h2>Editor\'s Note</h2>')
    editorial_paragraphs = editorial.split("\n\n")
    for para in editorial_paragraphs:
        para = para.strip()
        if para:
            html_parts.append(f'<p class="editorial">{para}</p>')
    html_parts.append('<hr>')

    # Papers
    html_parts.append('<h2>This Month\'s Papers & Posts</h2>')

    for i, paper in enumerate(papers, 1):
        title = paper.get("title", "Untitled")
        authors = format_authors(paper.get("authors", []))
        url = paper.get("url", "")
        published = paper.get("published", "")
        summary = paper.get("summary", "")
        venue = paper.get("venue", "")

        html_parts.append(f'<h3>{i}. {title}</h3>')

        meta_parts = []
        if authors != "Unknown authors":
            meta_parts.append(f"<strong>Authors:</strong> {authors}")
        if venue:
            meta_parts.append(f"<strong>Venue:</strong> {venue}")
        if published:
            meta_parts.append(f"<strong>Published:</strong> {published}")

        if meta_parts:
            html_parts.append(f'<p class="meta">{" · ".join(meta_parts)}</p>')

        if url:
            html_parts.append(f'<p class="paper-link">🔗 <a href="{url}">{url}</a></p>')

        if summary:
            summary_paragraphs = summary.split("\n\n")
            for para in summary_paragraphs:
                para = para.strip()
                if para:
                    html_parts.append(f'<p class="summary">{para}</p>')

        html_parts.append('<hr>')

    # Footer
    html_parts.append("""
<div class="footer">
<h2>About</h2>
<p><strong>Tokenization Digest</strong> is a monthly newsletter tracking research and developments 
in LLM tokenization. Whether you're a seasoned researcher or just getting started, we aim to keep 
you informed about what's happening in this foundational area of language modeling.</p>
<p><em>Have a paper, post, or project related to tokenization? Reply to this newsletter or reach out!</em></p>
</div>
</body>
</html>""")

    return "\n".join(html_parts)


if __name__ == "__main__":
    # Test with sample data
    test_papers = [
        {
            "title": "Tokenization Is More Than Compression",
            "authors": ["John Doe", "Jane Smith"],
            "abstract": "We study tokenization effects...",
            "url": "https://arxiv.org/abs/2024.12345",
            "published": "2025-01-15",
            "source": "arxiv",
            "summary": "This paper investigates how tokenization choices impact downstream performance beyond simple compression metrics. The authors find that morphologically rich languages are disproportionately affected by suboptimal tokenization.",
        },
    ]

    editorial = "This month brings a focused look at the downstream effects of tokenization choices. While compression ratio has long been the default metric for evaluating tokenizers, new work is pushing us to think more carefully about what we lose in the process."

    md = generate_markdown(test_papers, editorial)
    print("=== MARKDOWN ===")
    print(md[:500])
    print("...")

    html = generate_html(test_papers, editorial)
    print("\n=== HTML ===")
    print(html[:500])
    print("...")
