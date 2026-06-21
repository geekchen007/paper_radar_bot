"""Main orchestration entry point for paper_radar_bot."""

import logging
import sys
from datetime import datetime, timezone

from paper_radar_bot.arxiv_client import fetch_papers
from paper_radar_bot.config import load_config
from paper_radar_bot.renderer import render_report
from paper_radar_bot.summarizer import summarize
from paper_radar_bot.writer import write_report

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Fetch papers, summarize, render, and write the daily report."""
    config = load_config()

    date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    logger.info("Running paper radar for %s", date_str)

    logger.info("Fetching papers from arXiv (query: %s, max: %d)...", config.arxiv_query, config.arxiv_max_results)
    papers = fetch_papers(config)
    logger.info("Fetched %d papers.", len(papers))

    summaries = []
    for i, paper in enumerate(papers, start=1):
        logger.info("[%d/%d] Summarizing: %s", i, len(papers), paper.title[:60])
        summary = summarize(paper, config)
        if summary.error is not None:
            logger.warning("  Summary failed: %s", summary.error)
        summaries.append(summary)

    report = render_report(papers, summaries, query=config.arxiv_query, date_str=date_str)
    path = write_report(report, date_str)
    logger.info("Report written to: %s", path)


if __name__ == "__main__":
    main()
