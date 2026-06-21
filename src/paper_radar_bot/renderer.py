"""Render Paper records and Summaries into a Markdown report string."""

from paper_radar_bot.models import Paper, Summary, TopicResult


def render_paper_section(paper: Paper, summary: Summary) -> str:
    """Render a single paper and its summary as a Markdown section."""
    authors_str = "、".join(paper.authors) if paper.authors else "未知作者"
    published_date = paper.published[:10] if len(paper.published) >= 10 else paper.published

    lines = [
        f"## {paper.title}",
        "",
        f"- **作者：** {authors_str}",
        f"- **发布时间：** {published_date}",
        f"- **arXiv 链接：** [{paper.url}]({paper.url})",
        "",
    ]

    if summary.error is not None:
        lines += [
            "### 中文总结",
            "",
            f"> 总结失败：{summary.error}",
            "",
        ]
    else:
        lines += [
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
