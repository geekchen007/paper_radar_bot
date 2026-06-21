"""Render Paper records and Summaries into a Markdown report string."""

from paper_radar_bot.models import Paper, Summary


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


def render_report(
    papers: list[Paper],
    summaries: list[Summary],
    query: str,
    date_str: str,
) -> str:
    """Render all papers into a complete Markdown report."""
    header = "\n".join([
        f"# Paper Radar 日报 — {date_str}",
        "",
        "## 运行元信息",
        "",
        f"- **运行日期：** {date_str}",
        f"- **检索主题：** `{query}`",
        f"- **论文数量：** {len(papers)}",
        "",
        "---",
        "",
    ])

    sections = [render_paper_section(p, s) for p, s in zip(papers, summaries)]
    return header + "\n---\n\n".join(sections)
