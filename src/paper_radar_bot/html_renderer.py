"""Render multi-topic paper results into a single-file offline HTML report."""

from paper_radar_bot.models import Paper, Summary, TopicResult

_CSS = """\
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: system-ui, -apple-system, sans-serif;
    font-size: 15px; line-height: 1.6; color: #24292e;
}
.site-header {
    max-width: 1200px; margin: 0 auto; padding: 18px 16px 10px;
    border-bottom: 1px solid #e1e4e8;
}
h1 { font-size: 22px; font-weight: 600; margin-bottom: 4px; }
h2 {
    font-size: 17px; font-weight: 600; color: #0366d6;
    border-bottom: 1px solid #e1e4e8; padding-bottom: 5px; margin: 24px 0 10px;
}
h3 { font-size: 14px; font-weight: 600; margin-bottom: 2px; line-height: 1.45; }
.meta { color: #6a737d; font-size: 13px; }

/* ── Two-column layout ── */
.layout {
    display: grid;
    grid-template-columns: 230px 1fr;
    max-width: 1200px;
    margin: 0 auto;
    padding: 12px 16px 40px;
    align-items: start;
    gap: 0;
}

/* ── Sticky sidebar TOC ── */
.toc-sidebar {
    position: sticky;
    top: 12px;
    max-height: calc(100vh - 28px);
    overflow-y: auto;
    padding-right: 14px;
    border-right: 1px solid #e1e4e8;
}
.toc-title {
    font-size: 11px; font-weight: 700; color: #6a737d;
    text-transform: uppercase; letter-spacing: 0.6px;
    margin-bottom: 8px; padding-bottom: 5px;
    border-bottom: 1px solid #e1e4e8;
}
.toc-section { margin-bottom: 5px; }
.toc-section > summary {
    list-style: none; cursor: pointer; padding: 2px 0;
    font-size: 13px; font-weight: 600; color: #0366d6;
    display: flex; align-items: baseline; gap: 3px;
}
.toc-section > summary::-webkit-details-marker { display: none; }
.toc-section > summary .toc-arrow { font-size: 9px; flex-shrink: 0; }
.toc-section > summary a { color: #0366d6; text-decoration: none; }
.toc-section > summary a:hover { text-decoration: underline; }
.toc-count { font-size: 11px; font-weight: normal; color: #6a737d; margin-left: 2px; }
.toc-papers { list-style: none; padding-left: 11px; margin: 2px 0 4px; }
.toc-papers li { margin-bottom: 0; }
.toc-papers a {
    font-size: 11px; color: #586069; text-decoration: none;
    display: block; line-height: 1.5;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.toc-papers a:hover { color: #0366d6; text-decoration: underline; }

/* ── Main content ── */
.main-content { padding-left: 20px; }

/* ── Collapsible paper cards ── */
details.paper {
    border: 1px solid #e1e4e8; border-radius: 6px;
    margin-bottom: 8px; overflow: hidden;
    transition: box-shadow 0.15s;
}
details.paper:hover { box-shadow: 0 1px 4px rgba(0,0,0,.08); }
details.paper > summary {
    padding: 11px 36px 11px 13px;
    cursor: pointer; display: block;
    position: relative; user-select: none;
}
details.paper > summary::-webkit-details-marker { display: none; }
details.paper > summary::after {
    content: '▾'; font-size: 14px; color: #6a737d;
    position: absolute; right: 11px; top: 50%; transform: translateY(-50%);
}
details.paper[open] > summary::after { content: '▴'; }
details.paper > summary:hover { background: #f6f8fa; }
details.paper[open] > summary { background: #f6f8fa; }
.paper-body {
    padding: 12px 13px 14px;
    border-top: 1px solid #e1e4e8;
}

/* ── Typography inside cards ── */
.title-zh  { color: #586069; font-size: 13px; margin: 2px 0 5px; }
.one-line  { font-size: 13px; color: #444d56; margin-bottom: 7px; font-style: italic; }
.badges    { display: flex; flex-wrap: wrap; gap: 3px 4px; align-items: center; }
.badge {
    display: inline-block; font-size: 11px; padding: 1px 6px;
    border-radius: 10px; white-space: nowrap;
    background: #f1f8ff; color: #0366d6;
}
.badge.fresh  { background: #dcffe4; color: #22863a; }
.badge.recent { background: #ddf4ff; color: #0550ae; }
.badge.stars  { background: #fffbdd; color: #735c0f; }
.badge.old    { background: #f6f8fa; color: #6a737d; }
.badge.link   { background: #f1f8ff; color: #0366d6; text-decoration: none; cursor: pointer; }
.badge.link:hover { background: #dbedff; }
.tag { display: inline-block; font-size: 11px; padding: 1px 5px;
    border-radius: 3px; background: #f0f0f5; color: #586069; }
.abstract      { margin-bottom: 9px; font-size: 13.5px; }
.section-label { font-weight: 600; margin: 7px 0 2px; font-size: 12.5px; color: #444; }
ul  { padding-left: 17px; margin-bottom: 7px; }
li  { margin-bottom: 1px; font-size: 13.5px; }
.author-line { font-size: 12.5px; color: #586069; margin-bottom: 3px; }
.error { background: #f6f8fa; color: #6a737d; font-style: italic; padding: 8px;
    border-radius: 4px; font-size: 13px; }
.topic-count { font-size: 13px; font-weight: normal; color: #6a737d; }

/* ── Responsive ── */
@media (max-width: 680px) {
    .layout { grid-template-columns: 1fr; }
    .toc-sidebar {
        position: static; max-height: 200px;
        border-right: none; border-bottom: 1px solid #e1e4e8;
        padding-right: 0; padding-bottom: 8px;
        margin-bottom: 14px;
    }
    .main-content { padding-left: 0; }
}
"""


def _e(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _section_id(name: str) -> str:
    """Convert a topic name to a safe HTML anchor id."""
    sid = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")
    return sid if sid else "topic"


def _paper_id(arxiv_id: str) -> str:
    """Generate a stable HTML anchor id from arxiv_id, e.g. '2603.10495' → 'p-2603-10495'."""
    safe = "".join(c if c.isalnum() else "-" for c in arxiv_id)
    return f"p-{safe}"


def _list_html(items: list[str], label: str) -> str:
    if not items:
        return ""
    lis = "".join(f"<li>{_e(item)}</li>" for item in items)
    return f'<p class="section-label">{_e(label)}：</p><ul>{lis}</ul>'


def _freshness_badge(freshness_type: str, days: int) -> str:
    """Return a freshness badge <span> with a human-readable, relative-time label.

    Never uses a fixed "较早" label — always shows how long ago the paper was published,
    so readers can judge freshness for themselves.
    """
    if freshness_type == "new_submission":
        return '<span class="badge fresh">今日新投稿</span>'

    if freshness_type == "new_version":
        label = f"{days}天前" if days > 0 else "近期更新"
        return f'<span class="badge recent">{_e(label)}</span>'

    # "old" branch — show relative time instead of "较早论文"
    if days <= 0:
        label = "日期未知"
    elif days < 30:
        label = f"{days}天前"
    elif days < 365:
        months = max(1, round(days / 30))
        label = f"约{months}个月前"
    else:
        years = max(1, round(days / 365))
        label = f"约{years}年前"
    return f'<span class="badge old">{_e(label)}</span>'


def _render_template_paper(paper: Paper, summary: Summary) -> tuple[str, str]:
    """Return (summary_html, body_html) for a paper that has a full template report."""
    report = summary.report or {}
    paper_info = report.get("paper", {})
    automation = report.get("automation_fields", {})
    freshness = automation.get("freshness", {})
    credibility = automation.get("credibility_score", {})
    authors_block = report.get("authors", {})
    first_author = authors_block.get("first_author", {})
    advisor = authors_block.get("corresponding_advisor", {})
    group = authors_block.get("research_group", {})

    title_zh = paper_info.get("title_zh", "")
    one_line = paper_info.get("one_line_summary", "")
    freshness_type = freshness.get("type", "old")
    days = freshness.get("days_since_published", 0)
    stars = credibility.get("stars", 0)
    field_tags = paper_info.get("field_tags", [])

    title_zh_html = f'<p class="title-zh">{_e(title_zh)}</p>' if title_zh else ""
    one_line_html = f'<p class="one-line">{_e(one_line)}</p>' if one_line else ""
    tags_html = "".join(f'<span class="tag">{_e(t)}</span>' for t in field_tags)

    code_url = paper_info.get("code_url", "")
    data_url = paper_info.get("data_url", "")

    badge_parts = [
        _freshness_badge(freshness_type, days),
        f'<span class="badge stars">{stars} 星</span>',
        f'<a class="badge link" href="{_e(paper.url)}" target="_blank">arXiv ↗</a>',
        f'<span class="badge old">{_e(paper_info.get("published_date", paper.published[:10]))}</span>',
        f'<span class="badge old">{_e(paper_info.get("version", "v1"))}</span>',
    ]
    if code_url:
        badge_parts.append(f'<a class="badge link" href="{_e(code_url)}" target="_blank">代码 ↗</a>')
    if data_url:
        badge_parts.append(f'<a class="badge link" href="{_e(data_url)}" target="_blank">数据 ↗</a>')
    if tags_html:
        badge_parts.append(tags_html)

    badges_html = f'<div class="badges">{"".join(badge_parts)}</div>'

    # ── Summary (visible when collapsed) ──
    summary_html = (
        f'<h3>{_e(paper.title)}</h3>'
        f'{title_zh_html}'
        f'{one_line_html}'
        f'{badges_html}'
    )

    # ── Body (visible when expanded) ──
    author_lines = []
    if first_author.get("name"):
        author_lines.append(
            f"一作：{_e(first_author.get('name', ''))} · "
            f"{_e(first_author.get('affiliation', ''))}"
        )
    if advisor.get("name"):
        author_lines.append(
            f"导师：{_e(advisor.get('name', ''))} · {_e(advisor.get('title', ''))}"
        )
    if group.get("name"):
        author_lines.append(
            f"课题组：{_e(group.get('name', ''))} · {_e(group.get('institution', ''))}"
        )
    authors_html = "".join(f'<p class="author-line">{line}</p>' for line in author_lines)

    abstract = report.get("abstract_zh", summary.chinese_abstract)
    reading = report.get("reading_advice", "")
    rationale = credibility.get("rationale", "")

    body_html = (
        f'{authors_html}'
        f'<p class="abstract">{_e(abstract)}</p>'
        f'{_list_html(report.get("contributions", []), "核心贡献")}'
        f'{_list_html(report.get("key_results", []), "关键结果")}'
    )
    if reading:
        body_html += f'<p class="section-label">阅读建议：</p><p class="abstract">{_e(reading)}</p>'
    if rationale:
        body_html += f'<p class="section-label">可信度说明：</p><p class="abstract">{_e(rationale)}</p>'

    return summary_html, body_html


def _render_paper_fallback(paper: Paper, summary: Summary) -> tuple[str, str]:
    """Fallback for papers that have no structured template report."""
    authors_str = "、".join(paper.authors[:3]) if paper.authors else "未知作者"
    if len(paper.authors) > 3:
        authors_str += " 等"
    published_date = paper.published[:10] if len(paper.published) >= 10 else paper.published

    summary_html = (
        f'<h3>{_e(paper.title)}</h3>'
        f'<div class="badges">'
        f'<span class="badge old">{_e(authors_str)}</span>'
        f'<span class="badge old">{_e(published_date)}</span>'
        f'<a class="badge link" href="{_e(paper.url)}" target="_blank">arXiv ↗</a>'
        f'</div>'
    )

    highlights_html = ""
    if summary.highlights:
        items = "".join(f"<li>{_e(h)}</li>" for h in summary.highlights)
        highlights_html = f'<p class="section-label">关键亮点：</p><ul>{items}</ul>'
    applications_html = ""
    if summary.applications:
        items = "".join(f"<li>{_e(a)}</li>" for a in summary.applications)
        applications_html = f'<p class="section-label">潜在应用方向：</p><ul>{items}</ul>'

    body_html = (
        f'<p class="abstract">{_e(summary.chinese_abstract)}</p>'
        f'{highlights_html}{applications_html}'
    )
    return summary_html, body_html


def _render_paper(paper: Paper, summary: Summary) -> str:
    """Render a single paper as a collapsible <details> card."""
    pid = _paper_id(paper.arxiv_id)

    if summary.error is not None:
        summary_html = f'<h3>{_e(paper.title)}</h3>'
        body_html = f'<p class="error">总结失败：{_e(summary.error)}</p>'
    elif summary.report:
        summary_html, body_html = _render_template_paper(paper, summary)
    else:
        summary_html, body_html = _render_paper_fallback(paper, summary)

    return (
        f'<details class="paper" id="{pid}">'
        f'<summary>{summary_html}</summary>'
        f'<div class="paper-body">{body_html}</div>'
        f'</details>'
    )


def render_report(results: list[TopicResult], date_str: str, title: str = "Paper Radar 日报") -> str:
    """Render all topic results into a complete single-file HTML report."""
    total_papers = sum(len(r.papers) for r in results)

    # ── Sidebar TOC ──
    toc_sections = []
    for r in results:
        sid = _section_id(r.topic.name)
        paper_items = []
        for p in r.papers:
            pid = _paper_id(p.arxiv_id)
            label = p.title[:50] + "…" if len(p.title) > 50 else p.title
            paper_items.append(
                f'<li><a href="#{pid}" title="{_e(p.title)}">{_e(label)}</a></li>'
            )
        papers_list_html = "".join(paper_items)
        toc_sections.append(
            f'<details class="toc-section" open>'
            f'<summary>'
            f'<span class="toc-arrow">▾</span>'
            f'<a href="#{sid}">{_e(r.topic.name)}</a>'
            f'<span class="toc-count">（{len(r.papers)}篇）</span>'
            f'</summary>'
            f'<ul class="toc-papers">{papers_list_html}</ul>'
            f'</details>'
        )
    toc_html = "\n".join(toc_sections)

    # ── Main content sections ──
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
        f'<title>{_e(title)} — {_e(date_str)}</title>\n'
        f'<style>{_CSS}</style>\n'
        f'</head>\n'
        f'<body>\n'
        f'<div class="site-header">\n'
        f'<h1>{_e(title)} — {_e(date_str)}</h1>\n'
        f'<p class="meta">运行日期：{_e(date_str)} · '
        f'领域数：{len(results)} · 论文总数：{total_papers}</p>\n'
        f'</div>\n'
        f'<div class="layout">\n'
        f'<aside class="toc-sidebar">\n'
        f'<div class="toc-title">目录</div>\n'
        f'{toc_html}\n'
        f'</aside>\n'
        f'<div class="main-content">\n'
        f'{body}\n'
        f'</div>\n'
        f'</div>\n'
        f'</body>\n'
        f'</html>'
    )
