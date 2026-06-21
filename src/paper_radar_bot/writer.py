"""Create the reports directory and persist the report to disk."""

import os
import sys


def write_report(
    content: str,
    date_str: str,
    output_format: str = "html",
    reports_dir: str = "reports",
) -> str:
    """Write content to reports/<date_str>.<ext>; return the file path."""
    ext = "html" if output_format == "html" else "md"

    try:
        os.makedirs(reports_dir, exist_ok=True)
    except OSError as e:
        print(f"ERROR: Cannot create reports directory {reports_dir!r}: {e}", file=sys.stderr)
        sys.exit(1)

    file_path = os.path.join(reports_dir, f"{date_str}.{ext}")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as e:
        print(f"ERROR: Cannot write report to {file_path!r}: {e}", file=sys.stderr)
        sys.exit(1)

    return file_path
