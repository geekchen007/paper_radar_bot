"""Render Paper records and Summaries into a Markdown report string."""

from paper_radar_bot.models import Paper, Summary, TopicResult

_FRESHNESS_LABELS = {
    "new_submission": "今日新投稿",
    "new_version": "近期更新",
    "old": "较早论文",
}


def _list_block(items: list[str], label: str) -> list[str]:
    if not items:
        return []
    lines = [f"**{label}：**", ""]
    for item in items:
        lines.append(f"- {item}")
    lines.append("")
    return lines


def _render_template_section(paper: Paper, summary: Summary) -> str:
    """Render a paper using the paper_daily template structure."""
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
    freshness_label = _FRESHNESS_LABELS.get(freshness_type, freshness_type)
    stars = credibility.get("stars", 0)
    field_tags = paper_info.get("field_tags", [])

    lines = [
        f"## {paper.title}",
        "",
    ]
    if title_zh:
        lines.append(f"**中文标题：** {title_zh}")
        lines.append("")
    if one_line:
        lines.append(f"**一句话总结：** {one_line}")
        lines.append("")

    lines += [
        f"- **新鲜度：** {freshness_label}（{freshness.get('days_since_published', 0)} 天）",
        f"- **可信度：** {stars} 星",
        f"- **arXiv：** [{paper.url}]({paper.url}) · {paper_info.get('version', 'v1')}",
        f"- **发布时间：** {paper_info.get('published_date', paper.published[:10])}",
    ]
    if field_tags:
        lines.append(f"- **领域标签：** {', '.join(field_tags)}")
    code_url = paper_info.get("code_url", "")
    data_url = paper_info.get("data_url", "")
    if code_url:
        lines.append(f"- **代码：** [{code_url}]({code_url})")
    if data_url:
        lines.append(f"- **数据：** [{data_url}]({data_url})")
    lines.append("")

    if first_author.get("name"):
        lines.append(
            f"**一作：** {first_author.get('name')} · {first_author.get('affiliation', '')}"
        )
        lines.append("")
    if advisor.get("name"):
        lines.append(
            f"**导师/通讯：** {advisor.get('name')} · {advisor.get('title', '')}"
        )
        lines.append("")
    if group.get("name"):
        lines.append(f"**课题组：** {group.get('name')} · {group.get('institution', '')}")
        lines.append("")

    lines += ["### 中文摘要", "", report.get("abstract_zh", summary.chinese_abstract), "",]
    lines += _list_block(report.get("contributions", []), "核心贡献")
    lines += _list_block(report.get("key_results", []), "关键结果")

    reading = report.get("reading_advice", "")
    if reading:
        lines += ["**阅读建议：**", "", reading, ""]

    rationale = credibility.get("rationale", "")
    if rationale:
        lines += ["**可信度说明：**", "", rationale, ""]

    return "\n".join(lines)


def render_paper_section(paper: Paper, summary: Summary) -> str:
    """Render a single paper and its summary as a Markdown section."""
    if summary.error is not None:
        lines = [
            f"## {paper.title}",
            "",
            f"- **arXiv 链接：** [{paper.url}]({paper.url})",
            "",
            "### 中文总结",
            "",
            f"> 总结失败：{summary.error}",
            "",
        ]
        return "\n".join(lines)

    if summary.report:
        return _render_template_section(paper, summary)

    authors_str = "、".join(paper.authors) if paper.authors else "未知作者"
    published_date = paper.published[:10] if len(paper.published) >= 10 else paper.published

    lines = [
        f"## {paper.title}",
        "",
        f"- **作者：** {authors_str}",
        f"- **发布时间：** {published_date}",
        f"- **arXiv 链接：** [{paper.url}]({paper.url})",
        "",
        "### 中文总结",
        "",
        summary.chinese_abstract,
        "",
    ]

    if summary.highlights:
        lines += ["**关键亮点：**", ""]
        for h in summary.highlights:
            lines.append(f"- {h}")
        lines.append("")

    if summary.applications:
        lines += ["**潜在应用方向：**", ""]
        for a in summary.applications:
            lines.append(f"- {a}")
        lines.append("")

    return "\n".join(lines)


def render_report(results: list[TopicResult], date_str: str) -> str:
    """Render all topic results into a complete Markdown report."""
    total_papers = sum(len(r.papers) for r in results)

    header_lines = [
        f"# Paper Radar 日报 — {date_str}",
        "",
        "## 运行元信息",
        "",
        f"- **运行日期：** {date_str}",
        f"- **领域数量：** {len(results)}",
        f"- **论文总数：** {total_papers}",
        "",
        "---",
        "",
    ]

    topic_sections = []
    for result in results:
        paper_sections = [
            render_paper_section(p, s)
            for p, s in zip(result.papers, result.summaries)
        ]
        topic_header = f"# {result.topic.name}（{len(result.papers)} 篇）\n\n"
        topic_sections.append(topic_header + "\n---\n\n".join(paper_sections))

    return "\n".join(header_lines) + "\n\n---\n\n".join(topic_sections)
