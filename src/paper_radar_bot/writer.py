"""Create the reports directory and persist the report to disk."""

import os
import re
import sys

_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*]')


def _sanitize_filename_component(text: str) -> str:
    """Remove characters that are invalid on common filesystems."""
    cleaned = _INVALID_FILENAME_CHARS.sub("", text.strip())
    return cleaned or "默认"


def build_report_filename(report_title: str, date_str: str, output_format: str) -> str:
    """Build filename like prbXXX_20260621.html."""
    date_suffix = date_str.replace("-", "")
    safe_title = _sanitize_filename_component(report_title)
    ext = "html" if output_format == "html" else "md"
    return f"prb{safe_title}_{date_suffix}.{ext}"


def write_report(
    content: str,
    date_str: str,
    output_format: str = "html",
    reports_dir: str = "reports",
    report_title: str = "默认",
) -> str:
    """Write content to reports/prb<title>_<YYYYMMDD>.<ext>; return the file path."""
    ext = "html" if output_format == "html" else "md"

    try:
        os.makedirs(reports_dir, exist_ok=True)
    except OSError as e:
        print(f"ERROR: Cannot create reports directory {reports_dir!r}: {e}", file=sys.stderr)
        sys.exit(1)

    filename = build_report_filename(report_title, date_str, output_format)
    file_path = os.path.join(reports_dir, filename)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as e:
        print(f"ERROR: Cannot write report to {file_path!r}: {e}", file=sys.stderr)
        sys.exit(1)

    return file_path
