"""Unit tests for report file writing."""

import os
import tempfile

from paper_radar_bot.writer import write_report


def test_write_report_creates_file():
    with tempfile.TemporaryDirectory() as tmp:
        path = write_report("# Hello", "2026-06-21", output_format="html", reports_dir=tmp)
        assert os.path.isfile(path)


def test_write_report_correct_filename_html():
    with tempfile.TemporaryDirectory() as tmp:
        path = write_report("# Hello", "2026-06-21", output_format="html", reports_dir=tmp)
        assert os.path.basename(path) == "2026-06-21.html"


def test_write_report_correct_filename_markdown():
    with tempfile.TemporaryDirectory() as tmp:
        path = write_report("# Hello", "2026-06-21", output_format="markdown", reports_dir=tmp)
        assert os.path.basename(path) == "2026-06-21.md"


def test_write_report_file_content():
    with tempfile.TemporaryDirectory() as tmp:
        path = write_report("# Hello World", "2026-06-21", output_format="html", reports_dir=tmp)
        with open(path, encoding="utf-8") as f:
            assert f.read() == "# Hello World"


def test_write_report_creates_dir_if_missing():
    with tempfile.TemporaryDirectory() as tmp:
        subdir = os.path.join(tmp, "new_subdir")
        path = write_report("content", "2026-06-21", output_format="html", reports_dir=subdir)
        assert os.path.isfile(path)
