"""Unit tests for report file writing."""

import os
import tempfile

from paper_radar_bot.writer import build_report_filename, write_report


def test_build_report_filename_html():
    name = build_report_filename("图像文本翻译", "2026-06-21", "html")
    assert name == "prb图像文本翻译_20260621.html"


def test_build_report_filename_markdown():
    name = build_report_filename("测试主题", "2026-06-21", "markdown")
    assert name == "prb测试主题_20260621.md"


def test_write_report_creates_file():
    with tempfile.TemporaryDirectory() as tmp:
        path = write_report(
            "# Hello",
            "2026-06-21",
            output_format="html",
            reports_dir=tmp,
            report_title="图像文本翻译",
        )
        assert os.path.isfile(path)


def test_write_report_correct_filename_html():
    with tempfile.TemporaryDirectory() as tmp:
        path = write_report(
            "# Hello",
            "2026-06-21",
            output_format="html",
            reports_dir=tmp,
            report_title="图像文本翻译",
        )
        assert os.path.basename(path) == "prb图像文本翻译_20260621.html"


def test_write_report_correct_filename_markdown():
    with tempfile.TemporaryDirectory() as tmp:
        path = write_report(
            "# Hello",
            "2026-06-21",
            output_format="markdown",
            reports_dir=tmp,
            report_title="测试主题",
        )
        assert os.path.basename(path) == "prb测试主题_20260621.md"


def test_write_report_file_content():
    with tempfile.TemporaryDirectory() as tmp:
        path = write_report(
            "# Hello World",
            "2026-06-21",
            output_format="html",
            reports_dir=tmp,
            report_title="测试",
        )
        with open(path, encoding="utf-8") as f:
            assert f.read() == "# Hello World"


def test_write_report_creates_dir_if_missing():
    with tempfile.TemporaryDirectory() as tmp:
        subdir = os.path.join(tmp, "new_subdir")
        path = write_report(
            "content",
            "2026-06-21",
            output_format="html",
            reports_dir=subdir,
            report_title="测试",
        )
        assert os.path.isfile(path)
