"""Main orchestration entry point for paper_radar_bot."""

import logging
from datetime import datetime, timezone

from paper_radar_bot.arxiv_client import fetch_papers
from paper_radar_bot.config import load_config
from paper_radar_bot.html_renderer import render_report as render_html
from paper_radar_bot.models import TopicResult
from paper_radar_bot.renderer import render_report as render_markdown
from paper_radar_bot.summarizer import summarize
from paper_radar_bot.topics import load_topics
from paper_radar_bot.writer import write_report

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Fetch papers by topic, summarize, render, and write the daily report."""
    config = load_config()
    topics = load_topics(fallback_query=config.arxiv_query)

    date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    logger.info("Running paper radar for %s (%d topics, format: %s)", date_str, len(topics), config.output_format)

    results: list[TopicResult] = []
    for topic in topics:
        logger.info("Fetching topic %r (query: %s, max: %d)...", topic.name, topic.arxiv_query, topic.max_results)
        papers = fetch_papers(topic.arxiv_query, topic.max_results)
        logger.info("  Fetched %d papers.", len(papers))

        summaries = []
        for i, paper in enumerate(papers, start=1):
            logger.info("  [%d/%d] Summarizing: %s", i, len(papers), paper.title[:60])
            summary = summarize(paper, config)
            if summary.error is not None:
                logger.warning("    Summary failed: %s", summary.error)
            summaries.append(summary)

        results.append(TopicResult(topic=topic, papers=papers, summaries=summaries))

    if config.output_format == "html":
        report = render_html(results, date_str)
    else:
        report = render_markdown(results, date_str)

    path = write_report(report, date_str, output_format=config.output_format)
    logger.info("Report written to: %s", path)


if __name__ == "__main__":
    main()
