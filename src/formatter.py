"""Format the newsletter as Markdown and HTML for Substack."""

from datetime import datetime

ACADEMIC_SOURCES = ("arxiv", "semantic_scholar", "google_scholar")
NON_ACADEMIC_SOURCES = ("web", "lesswrong", "alignment_forum", "huggingface_blog")


def format_authors(authors: list[str], max_show: int = 3) -> str:
    """Format author list, truncating if too long."""
    if not authors:
        return ""
    if len(authors) <= max_show:
        return ", ".join(authors)
    return ", ".join(authors[:max_show]) + " et al."


def _split_by_type(papers: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split papers into academic papers and blog posts/other."""
    academic = []
    non_academic = []
    for p in papers:
        if p.get("source", "") in ACADEMIC_SOURCES:
            academic.append(p)
        else:
            non_academic.append(p)
    return academic, non_academic


def _format_item_markdown(paper: dict) -> str:
    """Format a single item as a Markdown entry with optional summary."""
    title = paper.get("title", "Untitled")
    authors = format_authors(paper.get("authors", []))
    url = paper.get("url", "")
    published = paper.get("published", "")
    summary = paper.get("summary", "")

    parts = []
    if url:
        parts.append(f"**[{title}]({url})**")
    else:
        parts.append(f"**{title}**")

    meta = []
    if authors:
        meta.append(authors)
    if published:
        meta.append(published)
    if meta:
        parts.append(" · ".join(meta))

    if summary:
        parts.append(summary)

    return "  \n".join(parts)


def _format_item_html(paper: dict) -> str:
    """Format a single item as HTML with optional summary."""
    title = paper.get("title", "Untitled")
    authors = format_authors(paper.get("authors", []))
    url = paper.get("url", "")
    published = paper.get("published", "")
    summary = paper.get("summary", "")

    html = ""
    if url:
        html += f'<p style="margin-bottom: 2px;"><strong><a href="{url}">{title}</a></strong></p>'
    else:
        html += f'<p style="margin-bottom: 2px;"><strong>{title}</strong></p>'

    meta = []
    if authors:
        meta.append(authors)
    if published:
        meta.append(published)
    if meta:
        html += f'<p class="meta" style="margin-top: 0;">{" · ".join(meta)}</p>'

    if summary:
        html += f'<p class="summary">{summary}</p>'

    return html


def generate_markdown(papers: list[dict], editorial: str = "", issue_number: int = 1, date: str = "", rest: list[dict] = None) -> str:
    """Generate the full newsletter as Markdown."""
    if not date:
        date = datetime.now().strftime("%B %Y")
    if rest is None:
        rest = []

    academic, non_academic = _split_by_type(papers)

    lines = []

    # Header
    lines.append(f"# Tokenization Digest — Issue #{issue_number}")
    lines.append(f"*{date}*")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Human's Pick
    lines.append("## \U0001f3c6 Human's Pick")
    lines.append("")
    lines.append("*[Your review goes here. Write about a paper, blog post, or project that caught your attention this month \u2014 it doesn't have to be from the list below.]*")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Papers section
    if academic:
        lines.append("## \U0001f4c4 Papers")
        lines.append("")
        for paper in academic:
            lines.append(f"- {_format_item_markdown(paper)}")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Blog posts & other section
    if non_academic:
        lines.append("## \U0001f4dd Blog Posts & Discussions")
        lines.append("")
        for post in non_academic:
            lines.append(f"- {_format_item_markdown(post)}")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Also Published (rest of papers, just links)
    if rest:
        lines.append("## \U0001f4da Also Published This Month")
        lines.append("")
        for paper in rest:
            title = paper.get("title", "Untitled")
            url = paper.get("url", "")
            authors = format_authors(paper.get("authors", []))
            if url:
                line = f"- [{title}]({url})"
            else:
                line = f"- {title}"
            if authors:
                line += f" — {authors}"
            lines.append(line)
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

    return "\n".join(lines)


def generate_html(papers: list[dict], editorial: str = "", issue_number: int = 1, date: str = "", rest: list[dict] = None) -> str:
    """Generate newsletter as HTML (Substack-compatible)."""
    if not date:
        date = datetime.now().strftime("%B %Y")
    if rest is None:
        rest = []

    academic, non_academic = _split_by_type(papers)

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
.subtitle {{ color: #888; font-style: italic; margin-bottom: 30px; }}
.meta {{ font-size: 13px; color: #888; margin-top: 0; margin-bottom: 15px; }}
.placeholder {{ color: #999; font-style: italic; padding: 20px; background: #f9f9f9; border-left: 3px solid #ddd; margin: 15px 0; }}
.item {{ margin-bottom: 12px; }}
.item a {{ color: #333; text-decoration: none; border-bottom: 1px solid #ccc; }}
.item a:hover {{ color: #000; border-bottom-color: #000; }}
.summary {{ font-size: 15px; color: #444; margin-top: 4px; margin-bottom: 15px; }}
hr {{ border: none; border-top: 1px solid #eee; margin: 25px 0; }}
.footer {{ font-size: 14px; color: #888; margin-top: 40px; }}
</style>
</head>
<body>
""")

    html_parts.append(f'<h1>Tokenization Digest &mdash; Issue #{issue_number}</h1>')
    html_parts.append(f'<p class="subtitle">{date}</p>')
    html_parts.append('<hr>')

    # Human's Pick
    html_parts.append('<h2>&#127942; Human\'s Pick</h2>')
    html_parts.append('<div class="placeholder">[Your review goes here. Write about a paper, blog post, or project that caught your attention this month &mdash; it doesn\'t have to be from the list below.]</div>')
    html_parts.append('<hr>')

    # Papers
    if academic:
        html_parts.append('<h2>&#128196; Papers</h2>')
        for paper in academic:
            html_parts.append(f'<div class="item">{_format_item_html(paper)}</div>')
        html_parts.append('<hr>')

    # Blog posts
    if non_academic:
        html_parts.append('<h2>&#128221; Blog Posts &amp; Discussions</h2>')
        for post in non_academic:
            html_parts.append(f'<div class="item">{_format_item_html(post)}</div>')
        html_parts.append('<hr>')

    # Also Published
    if rest:
        html_parts.append('<h2>&#128218; Also Published This Month</h2>')
        html_parts.append('<ul style="font-size: 15px; line-height: 1.8;">')
        for paper in rest:
            title = paper.get("title", "Untitled")
            url = paper.get("url", "")
            authors = format_authors(paper.get("authors", []))
            if url:
                entry = f'<a href="{url}">{title}</a>'
            else:
                entry = title
            if authors:
                entry += f' &mdash; <span style="color: #888;">{authors}</span>'
            html_parts.append(f'<li>{entry}</li>')
        html_parts.append('</ul>')
        html_parts.append('<hr>')

    # Footer
    html_parts.append("""
<div class="footer">
<p><strong>Tokenization Digest</strong> is a monthly newsletter tracking research and developments 
in LLM tokenization. Whether you're a seasoned researcher or just getting started, we aim to keep 
you informed about what's happening in this foundational area of language modeling.</p>
<p><em>Have a paper, post, or project related to tokenization? Reply to this newsletter or reach out!</em></p>
</div>
</body>
</html>""")

    return "\n".join(html_parts)
