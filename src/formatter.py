"""Format the newsletter as Markdown and HTML for Substack."""

from datetime import datetime


def format_authors(authors: list[str], max_show: int = 3) -> str:
    """Format author list, truncating if too long."""
    if not authors:
        return ""
    if len(authors) <= max_show:
        return ", ".join(authors)
    return ", ".join(authors[:max_show]) + " et al."


def _format_item_markdown(paper: dict, with_summary: bool = True) -> str:
    """Format a single item as Markdown."""
    title = paper.get("title", "Untitled")
    authors = format_authors(paper.get("authors", []))
    url = paper.get("url", "")
    published = paper.get("published", "")
    summary = paper.get("summary", "") if with_summary else ""

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
        parts.append(" \u00b7 ".join(meta))

    if summary:
        parts.append(summary)

    return "  \n".join(parts)


def _format_item_html(paper: dict, with_summary: bool = True) -> str:
    """Format a single item as HTML."""
    title = paper.get("title", "Untitled")
    authors = format_authors(paper.get("authors", []))
    url = paper.get("url", "")
    published = paper.get("published", "")
    summary = paper.get("summary", "") if with_summary else ""

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
        html += f'<p class="meta" style="margin-top: 0;">{" &middot; ".join(meta)}</p>'

    if summary:
        html += f'<p class="summary">{summary}</p>'

    return html


def generate_markdown(text_papers: list[dict] = None, text_blogs: list[dict] = None,
                      other_papers: list[dict] = None, rest: list[dict] = None,
                      issue_number: int = 1, date: str = "") -> str:
    """Generate the full newsletter as Markdown."""
    if not date:
        date = datetime.now().strftime("%B %Y")
    text_papers = text_papers or []
    text_blogs = text_blogs or []
    other_papers = other_papers or []
    rest = rest or []

    lines = []

    # Header
    lines.append(f"# Tokenization Digest \u2014 Issue #{issue_number}")
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

    # Text Processing Papers
    if text_papers:
        lines.append("## \U0001f4c4 Text Processing & Linguistics")
        lines.append("")
        for paper in text_papers:
            lines.append(f"### {paper.get('title', 'Untitled')}")
            lines.append("")
            meta = []
            authors = format_authors(paper.get("authors", []))
            if authors:
                meta.append(authors)
            if paper.get("published"):
                meta.append(paper["published"])
            if meta:
                lines.append(" \u00b7 ".join(meta))
                lines.append("")
            if paper.get("url"):
                lines.append(f"\U0001f517 [{paper['url']}]({paper['url']})")
                lines.append("")
            if paper.get("summary"):
                lines.append(paper["summary"])
                lines.append("")
            lines.append("---")
            lines.append("")

    # Text Blog Posts
    if text_blogs:
        lines.append("## \U0001f4dd Blog Posts & Discussions")
        lines.append("")
        for post in text_blogs:
            lines.append(f"### {post.get('title', 'Untitled')}")
            lines.append("")
            meta = []
            authors = format_authors(post.get("authors", []))
            if authors:
                meta.append(authors)
            if post.get("published"):
                meta.append(post["published"])
            if meta:
                lines.append(" \u00b7 ".join(meta))
                lines.append("")
            if post.get("url"):
                lines.append(f"\U0001f517 [{post['url']}]({post['url']})")
                lines.append("")
            if post.get("summary"):
                lines.append(post["summary"])
                lines.append("")
            lines.append("---")
            lines.append("")

    # Other Domain Papers
    if other_papers:
        lines.append("## \U0001f50a Tokenization Beyond Text")
        lines.append("")
        for paper in other_papers:
            lines.append(f"### {paper.get('title', 'Untitled')}")
            lines.append("")
            meta = []
            authors = format_authors(paper.get("authors", []))
            if authors:
                meta.append(authors)
            if paper.get("published"):
                meta.append(paper["published"])
            if meta:
                lines.append(" \u00b7 ".join(meta))
                lines.append("")
            if paper.get("url"):
                lines.append(f"\U0001f517 [{paper['url']}]({paper['url']})")
                lines.append("")
            if paper.get("summary"):
                lines.append(paper["summary"])
                lines.append("")
            lines.append("---")
            lines.append("")

    # Also Published
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
                line += f" \u2014 {authors}"
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


def generate_html(text_papers: list[dict] = None, text_blogs: list[dict] = None,
                   other_papers: list[dict] = None, rest: list[dict] = None,
                   issue_number: int = 1, date: str = "") -> str:
    """Generate newsletter as HTML (Substack-compatible)."""
    if not date:
        date = datetime.now().strftime("%B %Y")
    text_papers = text_papers or []
    text_blogs = text_blogs or []
    other_papers = other_papers or []
    rest = rest or []

    html_parts = []

    html_parts.append(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Tokenization Digest &mdash; Issue #{issue_number}</title>
<style>
body {{ font-family: Georgia, serif; max-width: 680px; margin: 0 auto; padding: 20px; color: #333; line-height: 1.6; }}
h1 {{ font-size: 28px; margin-bottom: 5px; }}
h2 {{ font-size: 22px; color: #555; border-bottom: 1px solid #ddd; padding-bottom: 8px; }}
h3 {{ font-size: 18px; margin-bottom: 5px; }}
.subtitle {{ color: #888; font-style: italic; margin-bottom: 30px; }}
.meta {{ font-size: 13px; color: #888; margin-top: 0; margin-bottom: 10px; }}
.placeholder {{ color: #999; font-style: italic; padding: 20px; background: #f9f9f9; border-left: 3px solid #ddd; margin: 15px 0; }}
.summary {{ font-size: 15px; color: #444; margin-top: 4px; margin-bottom: 15px; }}
.paper-link {{ font-size: 13px; margin-bottom: 8px; }}
.paper-link a {{ color: #666; }}
.item {{ margin-bottom: 20px; }}
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
    html_parts.append('<div class="placeholder">[Your review goes here.]</div>')
    html_parts.append('<hr>')

    # Text Processing Papers
    if text_papers:
        html_parts.append('<h2>&#128196; Text Processing &amp; Linguistics</h2>')
        for paper in text_papers:
            html_parts.append('<div class="item">')
            html_parts.append(f'<h3>{paper.get("title", "Untitled")}</h3>')
            meta = []
            authors = format_authors(paper.get("authors", []))
            if authors:
                meta.append(authors)
            if paper.get("published"):
                meta.append(paper["published"])
            if meta:
                html_parts.append(f'<p class="meta">{" &middot; ".join(meta)}</p>')
            if paper.get("url"):
                html_parts.append(f'<p class="paper-link">&#128279; <a href="{paper["url"]}">{paper["url"]}</a></p>')
            if paper.get("summary"):
                html_parts.append(f'<p class="summary">{paper["summary"]}</p>')
            html_parts.append('</div>')
        html_parts.append('<hr>')

    # Text Blog Posts
    if text_blogs:
        html_parts.append('<h2>&#128221; Blog Posts &amp; Discussions</h2>')
        for post in text_blogs:
            html_parts.append('<div class="item">')
            html_parts.append(f'<h3>{post.get("title", "Untitled")}</h3>')
            meta = []
            authors = format_authors(post.get("authors", []))
            if authors:
                meta.append(authors)
            if post.get("published"):
                meta.append(post["published"])
            if meta:
                html_parts.append(f'<p class="meta">{" &middot; ".join(meta)}</p>')
            if post.get("url"):
                html_parts.append(f'<p class="paper-link">&#128279; <a href="{post["url"]}">{post["url"]}</a></p>')
            if post.get("summary"):
                html_parts.append(f'<p class="summary">{post["summary"]}</p>')
            html_parts.append('</div>')
        html_parts.append('<hr>')

    # Other Domain Papers
    if other_papers:
        html_parts.append('<h2>&#128266; Tokenization Beyond Text</h2>')
        for paper in other_papers:
            html_parts.append('<div class="item">')
            html_parts.append(f'<h3>{paper.get("title", "Untitled")}</h3>')
            meta = []
            authors = format_authors(paper.get("authors", []))
            if authors:
                meta.append(authors)
            if paper.get("published"):
                meta.append(paper["published"])
            if meta:
                html_parts.append(f'<p class="meta">{" &middot; ".join(meta)}</p>')
            if paper.get("url"):
                html_parts.append(f'<p class="paper-link">&#128279; <a href="{paper["url"]}">{paper["url"]}</a></p>')
            if paper.get("summary"):
                html_parts.append(f'<p class="summary">{paper["summary"]}</p>')
            html_parts.append('</div>')
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
