"""Unit tests for HTML rendering."""

from paper_radar_bot.html_renderer import render_report
from paper_radar_bot.models import Paper, Summary, Topic, TopicResult

_PAPER = Paper(
    title="Test Paper",
    authors=["Alice", "Bob"],
    published="2026-06-21T00:00:00Z",
    arxiv_id="2406.00001",
    abstract="This paper tests the renderer.",
    url="https://arxiv.org/abs/2406.00001",
)

_SUMMARY = Summary(
    chinese_abstract="这是一篇关于渲染器的测试论文。",
    highlights=["亮点 A", "亮点 B"],
    applications=["应用 X"],
)

_FAILED_SUMMARY = Summary(
    chinese_abstract="",
    highlights=[],
    applications=[],
    error="network timeout",
)

_TOPIC = Topic(name="AI 基础", keywords=["artificial intelligence"], max_results=5)
_RESULT = TopicResult(topic=_TOPIC, papers=[_PAPER], summaries=[_SUMMARY])
_RESULT_FAILED = TopicResult(topic=_TOPIC, papers=[_PAPER], summaries=[_FAILED_SUMMARY])


def test_render_report_contains_date():
    html = render_report([_RESULT], date_str="2026-06-21")
    assert "2026-06-21" in html


def test_render_report_contains_topic_name():
    html = render_report([_RESULT], date_str="2026-06-21")
    assert "AI 基础" in html


def test_render_report_contains_paper_title():
    html = render_report([_RESULT], date_str="2026-06-21")
    assert "Test Paper" in html


def test_render_report_contains_arxiv_url():
    html = render_report([_RESULT], date_str="2026-06-21")
    assert "https://arxiv.org/abs/2406.00001" in html


def test_render_report_contains_chinese_abstract():
    html = render_report([_RESULT], date_str="2026-06-21")
    assert "这是一篇关于渲染器的测试论文。" in html


def test_render_report_failed_summary_shows_error():
    html = render_report([_RESULT_FAILED], date_str="2026-06-21")
    assert "总结失败" in html
    assert "network timeout" in html


def test_render_report_multiple_topics():
    topic2 = Topic(name="机器学习", keywords=["machine learning"], max_results=5)
    result2 = TopicResult(topic=topic2, papers=[_PAPER], summaries=[_SUMMARY])
    html = render_report([_RESULT, result2], date_str="2026-06-21")
    assert "AI 基础" in html
    assert "机器学习" in html
