"""Generate Chinese summaries for papers via OpenAI-compatible Chat Completions."""

import json
import logging

from openai import OpenAI, OpenAIError

from paper_radar_bot.config import Config
from paper_radar_bot.models import Paper, Summary
from paper_radar_bot.paper_template import get_system_prompt, merge_paper_report

logger = logging.getLogger(__name__)


def summarize(paper: Paper, config: Config, report_date: str) -> Summary:
    """Call LLM to generate a structured Chinese summary; return Summary with error on failure."""
    client = OpenAI(api_key=config.api_key, base_url=config.base_url)
    user_message = (
        f"报告日期：{report_date}\n"
        f"论文标题：{paper.title}\n"
        f"arXiv ID：{paper.arxiv_id}\n"
        f"作者：{', '.join(paper.authors)}\n"
        f"发布时间：{paper.published}\n"
        f"摘要（英文）：{paper.abstract}"
    )

    try:
        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": get_system_prompt()},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or ""
        data = json.loads(raw)
        report = merge_paper_report(
            paper_title=paper.title,
            paper_authors=paper.authors,
            published=paper.published,
            arxiv_id=paper.arxiv_id,
            url=paper.url,
            report_date=report_date,
            llm_data=data,
        )
        abstract_zh = report.get("abstract_zh", "")
        contributions = report.get("contributions", [])
        field_tags = report.get("paper", {}).get("field_tags", [])
        return Summary(
            chinese_abstract=abstract_zh,
            highlights=contributions,
            applications=field_tags,
            report=report,
        )
    except (OpenAIError, json.JSONDecodeError, KeyError, IndexError) as e:
        logger.warning("Summarization failed for paper %r: %s", paper.arxiv_id, e)
        return Summary(
            chinese_abstract="",
            highlights=[],
            applications=[],
            error=str(e),
        )


_TRANSLATE_SYSTEM = (
    "你是专业的学术论文翻译助手。"
    "将英文摘要翻译为流畅准确的中文，保持学术用语，不添加额外解释或内容。"
)


def translate_abstract(paper: Paper, config: Config) -> Summary:
    """Translate paper abstract to Chinese; return Summary with only chinese_abstract set."""
    client = OpenAI(api_key=config.api_key, base_url=config.base_url)
    user_message = f"请将以下英文论文摘要翻译为中文：\n\n{paper.abstract}"

    try:
        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": _TRANSLATE_SYSTEM},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
        )
        chinese_abstract = (response.choices[0].message.content or "").strip()
        return Summary(chinese_abstract=chinese_abstract, highlights=[], applications=[])
    except (OpenAIError, IndexError) as e:
        logger.warning("Translation failed for paper %r: %s", paper.arxiv_id, e)
        return Summary(chinese_abstract="", highlights=[], applications=[], error=str(e))
