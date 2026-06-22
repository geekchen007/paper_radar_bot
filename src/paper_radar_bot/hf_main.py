"""Entry point for the HuggingFace trending papers report."""

import logging
from datetime import datetime, timezone

from paper_radar_bot.arxiv_client import fetch_papers_by_ids
from paper_radar_bot.config import Config, load_config
from paper_radar_bot.hf_client import fetch_daily_ids, fetch_weekly_ids
from paper_radar_bot.html_renderer import render_report
from paper_radar_bot.models import Summary, Topic, TopicResult
from paper_radar_bot.summarizer import summarize, translate_abstract
from paper_radar_bot.writer import write_report

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

_HF_REPORT_TITLE = "HF热门论文"
_REPORT_DISPLAY_TITLE = "HuggingFace 热门论文"


def _process_section(
    label: str,
    arxiv_ids: list[str],
    config: Config,
    date_str: str,
) -> TopicResult:
    """Fetch papers and generate summaries for one section (daily or weekly)."""
    topic = Topic(name=label, keywords=[], max_results=len(arxiv_ids))

    if not arxiv_ids:
        logger.warning("No IDs for section %r, section will be empty.", label)
        return TopicResult(topic=topic, papers=[], summaries=[])

    logger.info("  Fetching %d papers from arXiv...", len(arxiv_ids))
    papers = fetch_papers_by_ids(arxiv_ids)
    logger.info("  Retrieved %d papers.", len(papers))

    summaries: list[Summary] = []
    for i, paper in enumerate(papers, start=1):
        logger.info("  [%d/%d] Processing: %s", i, len(papers), paper.title[:60])
        if config.hf_summarize_mode == "full":
            summary = summarize(paper, config, date_str)
        else:
            summary = translate_abstract(paper, config)
        if summary.error is not None:
            logger.warning("    Failed: %s", summary.error)
        summaries.append(summary)

    return TopicResult(topic=topic, papers=papers, summaries=summaries)


def main() -> None:
    """Fetch HF trending papers, translate, render, and write the report."""
    config = load_config()
    date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    logger.info(
        "HF trending report for %s (mode: %s)",
        date_str,
        config.hf_summarize_mode,
    )

    logger.info("Fetching HuggingFace daily top 10...")
    daily_ids = fetch_daily_ids(top_n=10)
    logger.info("Found %d daily IDs.", len(daily_ids))

    logger.info("Fetching HuggingFace weekly trending top 10...")
    weekly_ids = fetch_weekly_ids(top_n=10)
    logger.info("Found %d weekly IDs.", len(weekly_ids))

    daily_result = _process_section("HuggingFace 每日 Top 10", daily_ids, config, date_str)
    weekly_result = _process_section("HuggingFace 每周 Top 10", weekly_ids, config, date_str)

    results = [daily_result, weekly_result]
    report = render_report(results, date_str, title=_REPORT_DISPLAY_TITLE)
    path = write_report(
        report,
        date_str,
        output_format="html",
        report_title=_HF_REPORT_TITLE,
    )
    logger.info("Report written to: %s", path)


if __name__ == "__main__":
    main()
