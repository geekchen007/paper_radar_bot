"""Render multi-topic paper results into a single-file offline HTML report."""

from paper_radar_bot.models import Paper, Summary, TopicResult

_CSS = """\
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: system-ui, -apple-system, sans-serif;
    font-size: 16px; line-height: 1.6; color: #24292e;
    max-width: 860px; margin: 0 auto; padding: 24px 16px;
}
h1 { font-size: 24px; font-weight: 600; margin-bottom: 8px; }
h2 {
    font-size: 20px; font-weight: 600; color: #0366d6;
    border-bottom: 1px solid #e1e4e8; padding-bottom: 6px; margin: 32px 0 16px;
}
h3 { font-size: 16px; font-weight: 600; margin-bottom: 4px; }
.meta { color: #6a737d; font-size: 14px; margin-bottom: 16px; }
nav { margin: 16px 0; font-size: 14px; }
nav a { color: #0366d6; text-decoration: none; margin-right: 4px; }
nav a:hover { text-decoration: underline; }
nav span.sep { color: #6a737d; margin-right: 4px; }
.paper { border: 1px solid #e1e4e8; border-radius: 4px; padding: 16px; margin-bottom: 16px; }
.paper-meta { color: #6a737d; font-size: 14px; margin-bottom: 8px; }
.paper-meta a { color: #0366d6; text-decoration: none; }
.paper-meta a:hover { text-decoration: underline; }
.abstract { margin-bottom: 12px; }
.section-label { font-weight: 600; margin: 8px 0 4px; }
ul { padding-left: 20px; margin-bottom: 8px; }
li { margin-bottom: 2px; }
.error { background: #f6f8fa; color: #6a737d; font-style: italic; padding: 8px; border-radius: 4px; }
hr { border: none; border-top: 1px solid #e1e4e8; margin: 24px 0; }
.topic-count { font-size: 14px; font-weight: normal; color: #6a737d; }
"""


def _e(text: str) -> str:
    """Escape HTML special characters."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _section_id(name: str) -> str:
    """Convert a topic name to a safe HTML id; falls back to 'topic' if name is all punctuation."""
    sid = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")
    return sid if sid else "topic"


def _render_paper(paper: Paper, summary: Summary) -> str:
    """Render a single paper as an HTML article."""
    authors_str = "、".join(paper.authors) if paper.authors else "未知作者"
    published_date = paper.published[:10] if len(paper.published) >= 10 else paper.published

    if summary.error is not None:
        body = f'<p class="error">总结失败：{_e(summary.error)}</p>'
    else:
        highlights_html = ""
        if summary.highlights:
            items = "".join(f"<li>{_e(h)}</li>" for h in summary.highlights)
            highlights_html = f'<p class="section-label">关键亮点：</p><ul>{items}</ul>'
        applications_html = ""
        if summary.applications:
            items = "".join(f"<li>{_e(a)}</li>" for a in summary.applications)
            applications_html = f'<p class="section-label">潜在应用方向：</p><ul>{items}</ul>'
        body = f'<p class="abstract">{_e(summary.chinese_abstract)}</p>{highlights_html}{applications_html}'

    return (
        f'<article class="paper">'
        f'<h3>{_e(paper.title)}</h3>'
        f'<p class="paper-meta">{_e(authors_str)} · {_e(published_date)} · '
        f'<a href="{_e(paper.url)}" target="_blank">arXiv</a></p>'
        f'{body}'
        f'</article>'
    )


def render_report(results: list[TopicResult], date_str: str) -> str:
    """Render all topic results into a complete single-file HTML report."""
    total_papers = sum(len(r.papers) for r in results)

    nav_parts = []
    for i, r in enumerate(results):
        if i > 0:
            nav_parts.append('<span class="sep">|</span>')
        nav_parts.append(f'<a href="#{_section_id(r.topic.name)}">{_e(r.topic.name)}</a>')
    nav_html = "".join(nav_parts)

    sections = []
    for r in results:
        sid = _section_id(r.topic.name)
        papers_html = "".join(_render_paper(p, s) for p, s in zip(r.papers, r.summaries))
        sections.append(
            f'<section id="{sid}">'
            f'<h2>{_e(r.topic.name)} '
            f'<span class="topic-count">（{len(r.papers)} 篇）</span></h2>'
            f'{papers_html}'
            f'</section>'
        )

    body = "\n".join(sections)

    return (
        f'<!DOCTYPE html>\n'
        f'<html lang="zh-CN">\n'
        f'<head>\n'
        f'<meta charset="UTF-8">\n'
        f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>Paper Radar 日报 — {_e(date_str)}</title>\n'
        f'<style>{_CSS}</style>\n'
        f'</head>\n'
        f'<body>\n'
        f'<h1>Paper Radar 日报 — {_e(date_str)}</h1>\n'
        f'<p class="meta">运行日期：{_e(date_str)} · 领域数：{len(results)} · 论文总数：{total_papers}</p>\n'
        f'<nav>{nav_html}</nav>\n'
        f'<hr>\n'
        f'{body}\n'
        f'</body>\n'
        f'</html>'
    )
