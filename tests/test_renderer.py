"""Unit tests for Markdown rendering."""

from paper_radar_bot.models import Paper, Summary
from paper_radar_bot.renderer import render_paper_section, render_report

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


def test_render_paper_section_contains_title():
    section = render_paper_section(_PAPER, _SUMMARY)
    assert "Test Paper" in section


def test_render_paper_section_contains_authors():
    section = render_paper_section(_PAPER, _SUMMARY)
    assert "Alice" in section
    assert "Bob" in section


def test_render_paper_section_contains_url():
    section = render_paper_section(_PAPER, _SUMMARY)
    assert "https://arxiv.org/abs/2406.00001" in section


def test_render_paper_section_contains_chinese_abstract():
    section = render_paper_section(_PAPER, _SUMMARY)
    assert "这是一篇关于渲染器的测试论文。" in section


def test_render_paper_section_contains_highlights():
    section = render_paper_section(_PAPER, _SUMMARY)
    assert "亮点 A" in section
    assert "亮点 B" in section


def test_render_paper_section_contains_applications():
    section = render_paper_section(_PAPER, _SUMMARY)
    assert "应用 X" in section


def test_render_paper_section_failed_summary_shows_error():
    section = render_paper_section(_PAPER, _FAILED_SUMMARY)
    assert "总结失败" in section or "network timeout" in section


def test_render_report_contains_date():
    report = render_report([_PAPER], [_SUMMARY], query="cat:cs.AI", date_str="2026-06-21")
    assert "2026-06-21" in report


def test_render_report_contains_query():
    report = render_report([_PAPER], [_SUMMARY], query="cat:cs.AI", date_str="2026-06-21")
    assert "cat:cs.AI" in report


def test_render_report_contains_paper_count():
    report = render_report([_PAPER], [_SUMMARY], query="cat:cs.AI", date_str="2026-06-21")
    assert "1" in report
