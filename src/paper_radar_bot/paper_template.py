"""Load paper_daily template and merge LLM output with arXiv metadata."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

_TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "templates" / "paper_daily.md"

_LLM_JSON_SCHEMA = """{
  "title_zh": "中文标题",
  "one_line_summary": "一句话核心贡献",
  "field_tags": ["领域标签1", "领域标签2"],
  "code_url": "代码链接或空字符串",
  "data_url": "数据链接或空字符串",
  "authors": {
    "first_author": {"name": "", "affiliation": "", "role": ""},
    "corresponding_advisor": {
      "name": "", "title": "", "research_focus": "", "homepage": ""
    },
    "research_group": {
      "name": "", "institution": "", "notable_works": [], "influence_signals": []
    }
  },
  "abstract_zh": "中文摘要式总结",
  "contributions": ["贡献1", "贡献2"],
  "key_results": ["关键结果1"],
  "reading_advice": "阅读建议",
  "credibility_score": {
    "stars": 3.5,
    "breakdown": {
      "group_influence": 1.0,
      "open_source": 0.75,
      "experiment_completeness": 1.0
    },
    "rationale": "评分理由"
  }
}"""

_SYSTEM_PROMPT = (
    "你是一名专业的 AI 研究助手。请用中文对论文进行深度解读，"
    "严格按照 JSON 格式输出，不要包含任何额外文字。\n"
    "credibility_score 满分 5 星：group_influence 0-2、open_source 0-1.5、"
    "experiment_completeness 0-1.5，三项相加四舍五入到 0.5 星为 stars。\n"
    "若信息不足，相关字段留空字符串或空数组，不要编造链接。\n"
    f"JSON 结构：\n{_LLM_JSON_SCHEMA}"
)


def get_system_prompt() -> str:
    """Return the LLM system prompt aligned with templates/paper_daily.md."""
    if _TEMPLATE_PATH.exists():
        return _SYSTEM_PROMPT
    return _SYSTEM_PROMPT


def _parse_date(value: str) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _arxiv_version(arxiv_id: str) -> str:
    match = re.search(r"v(\d+)$", arxiv_id)
    return f"v{match.group(1)}" if match else "v1"


def compute_freshness(published: str, report_date: str) -> dict:
    """Compute freshness.type and days_since_published from arXiv published time."""
    pub_dt = _parse_date(published)
    try:
        report_dt = datetime.strptime(report_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        report_dt = datetime.now(tz=timezone.utc)

    if pub_dt is None:
        return {"type": "old", "days_since_published": 0}

    if pub_dt.tzinfo is None:
        pub_dt = pub_dt.replace(tzinfo=timezone.utc)
    days = max(0, (report_dt.date() - pub_dt.date()).days)

    if days == 0:
        freshness_type = "new_submission"
    elif days <= 14:
        freshness_type = "new_version"
    else:
        freshness_type = "old"

    return {"type": freshness_type, "days_since_published": days}


def merge_paper_report(
    paper_title: str,
    paper_authors: list[str],
    published: str,
    arxiv_id: str,
    url: str,
    report_date: str,
    llm_data: dict,
) -> dict:
    """Merge arXiv metadata with LLM-filled fields into the full paper_daily schema."""
    authors_block = llm_data.get("authors") or {}
    credibility = llm_data.get("credibility_score") or {}
    breakdown = credibility.get("breakdown") or {}

    first_author = authors_block.get("first_author") or {}
    if not first_author.get("name") and paper_authors:
        first_author = {
            "name": paper_authors[0],
            "affiliation": first_author.get("affiliation", ""),
            "role": first_author.get("role", ""),
        }

    return {
        "report_date": report_date,
        "paper": {
            "title": paper_title,
            "title_zh": llm_data.get("title_zh", ""),
            "one_line_summary": llm_data.get("one_line_summary", ""),
            "arxiv_id": arxiv_id,
            "url": url,
            "published_date": published[:10] if len(published) >= 10 else published,
            "version": _arxiv_version(arxiv_id),
            "field_tags": llm_data.get("field_tags", []),
            "code_url": llm_data.get("code_url", ""),
            "data_url": llm_data.get("data_url", ""),
        },
        "authors": {
            "first_author": first_author,
            "corresponding_advisor": authors_block.get("corresponding_advisor") or {},
            "research_group": authors_block.get("research_group") or {},
        },
        "abstract_zh": llm_data.get("abstract_zh", ""),
        "contributions": llm_data.get("contributions", []),
        "key_results": llm_data.get("key_results", []),
        "reading_advice": llm_data.get("reading_advice", ""),
        "automation_fields": {
            "freshness": compute_freshness(published, report_date),
            "credibility_score": {
                "stars": credibility.get("stars", 0),
                "breakdown": {
                    "group_influence": breakdown.get("group_influence", 0),
                    "open_source": breakdown.get("open_source", 0),
                    "experiment_completeness": breakdown.get("experiment_completeness", 0),
                },
                "rationale": credibility.get("rationale", ""),
            },
        },
    }
