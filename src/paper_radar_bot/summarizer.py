"""Generate Chinese summaries for papers via OpenAI-compatible Chat Completions."""

import json
import logging

from openai import OpenAI, OpenAIError

from paper_radar_bot.config import Config
from paper_radar_bot.models import Paper, Summary

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "你是一名专业的 AI 研究助手。请用中文对以下论文进行结构化总结，"
    "严格按照 JSON 格式输出，不要包含任何额外文字。\n"
    "JSON 结构：\n"
    '{\n'
    '  "chinese_abstract": "一段话总结论文核心内容",\n'
    '  "highlights": ["亮点1", "亮点2", "亮点3"],\n'
    '  "applications": ["应用方向1", "应用方向2"]\n'
    '}'
)


def summarize(paper: Paper, config: Config) -> Summary:
    """Call LLM to generate a structured Chinese summary; return Summary with error on failure."""
    client = OpenAI(api_key=config.api_key, base_url=config.base_url)
    user_message = (
        f"论文标题：{paper.title}\n"
        f"作者：{', '.join(paper.authors)}\n"
        f"摘要（英文）：{paper.abstract}"
    )

    try:
        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or ""
        data = json.loads(raw)
        return Summary(
            chinese_abstract=data.get("chinese_abstract", ""),
            highlights=data.get("highlights", []),
            applications=data.get("applications", []),
        )
    except (OpenAIError, json.JSONDecodeError, KeyError, IndexError) as e:
        logger.warning("Summarization failed for paper %r: %s", paper.arxiv_id, e)
        return Summary(
            chinese_abstract="",
            highlights=[],
            applications=[],
            error=str(e),
        )
