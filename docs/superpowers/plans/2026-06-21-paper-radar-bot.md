# Paper Radar Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI that fetches recent arXiv papers by topic, generates Chinese summaries via OpenAI-compatible API, and outputs a dated Markdown report — runnable locally via `.bat` and automatically via GitHub Actions.

**Architecture:** Seven focused modules under `src/paper_radar_bot/` handle config loading, data models, arXiv fetching, LLM summarization, Markdown rendering, and file writing; `main.py` wires them together. Tests cover pure-logic modules (parser, renderer, writer) only; external HTTP calls are verified manually or via Actions.

**Tech Stack:** Python 3.11+, `requests`, `python-dotenv`, `openai` SDK, `pytest`, GitHub Actions

## Global Constraints

- Python ≥ 3.11 (uses built-in `tomllib`, union types, match statements are allowed)
- All source lives under `src/paper_radar_bot/`; tests under `tests/`
- Public functions/methods must have type annotations and docstrings
- No `from module import *`; each import on its own line
- Line length ≤ 120 characters
- `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants
- No bare `except:`; always catch specific exceptions and at minimum log them
- f-strings preferred; `is`/`is not` for `None` comparisons
- Commit message format: `<type>(<scope>): <subject>` (see CLAUDE.md)

---

## File Map

| File | Role |
|------|------|
| `src/paper_radar_bot/__init__.py` | Package marker |
| `src/paper_radar_bot/config.py` | Load & validate env vars; expose typed `Config` dataclass |
| `src/paper_radar_bot/models.py` | `Paper` and `Summary` dataclasses |
| `src/paper_radar_bot/arxiv_client.py` | Fetch & parse arXiv Atom feed → `list[Paper]` |
| `src/paper_radar_bot/summarizer.py` | Call OpenAI-compatible Chat Completions → `Summary` |
| `src/paper_radar_bot/renderer.py` | `Paper` + `Summary` → Markdown string |
| `src/paper_radar_bot/writer.py` | Create `reports/` dir, write report file |
| `src/paper_radar_bot/main.py` | Orchestration entry point |
| `tests/__init__.py` | Package marker |
| `tests/test_arxiv_client.py` | Unit tests for Atom XML parsing |
| `tests/test_renderer.py` | Unit tests for Markdown rendering |
| `tests/test_writer.py` | Unit tests for path generation & file writing |
| `.env.example` | Documented template of all env vars |
| `requirements.txt` | Pinned runtime dependencies |
| `run_paper_radar.bat` | Windows one-click launcher |
| `.github/workflows/paper_radar.yml` | Scheduled + manual GitHub Actions workflow |
| `reports/.gitkeep` | Keep `reports/` in git without committing reports |

---

### Task 1: Project Scaffold & Dependencies

**Files:**
- Create: `src/paper_radar_bot/__init__.py`
- Create: `tests/__init__.py`
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `reports/.gitkeep`
- Create: `.gitignore`

**Interfaces:**
- Produces: installable package at `src/paper_radar_bot`; `requirements.txt` used by all subsequent tasks

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p src/paper_radar_bot tests reports
touch src/paper_radar_bot/__init__.py
touch tests/__init__.py
touch reports/.gitkeep
```

- [ ] **Step 2: Write `requirements.txt`**

```
requests==2.32.3
python-dotenv==1.0.1
openai==1.35.10
pytest==8.2.2
```

- [ ] **Step 3: Write `.env.example`**

```dotenv
# Required
OPENAI_API_KEY=sk-...

# Optional — defaults shown
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
ARXIV_QUERY=cat:cs.AI OR cat:cs.LG OR cat:cs.CL
ARXIV_MAX_RESULTS=10
REPORT_TIMEZONE=Asia/Shanghai
REPORT_LOCALE=zh_CN
```

- [ ] **Step 4: Write `.gitignore`**

```gitignore
__pycache__/
*.pyc
*.pyo
.env
*.egg-info/
dist/
build/
.venv/
venv/
reports/*.md
```

- [ ] **Step 5: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: all packages install without errors.

- [ ] **Step 6: Verify package is importable**

```bash
python -c "import paper_radar_bot; print('ok')"
```

Expected output: `ok`

Wait — the package is under `src/`, so the import needs `PYTHONPATH=src`. Adjust:

```bash
PYTHONPATH=src python -c "import paper_radar_bot; print('ok')"
```

Expected output: `ok`

- [ ] **Step 7: Commit**

```bash
git add src/paper_radar_bot/__init__.py tests/__init__.py requirements.txt .env.example reports/.gitkeep .gitignore
git commit -m "chore(scaffold): initialize package structure and dependencies"
```

---

### Task 2: Data Models (`models.py`)

**Files:**
- Create: `src/paper_radar_bot/models.py`

**Interfaces:**
- Produces:
  - `Paper(title: str, authors: list[str], published: str, arxiv_id: str, abstract: str, url: str)`
  - `Summary(chinese_abstract: str, highlights: list[str], applications: list[str], error: str | None = None)`

- [ ] **Step 1: Write `models.py`**

```python
"""Shared data structures for paper records and summaries."""

from dataclasses import dataclass, field


@dataclass
class Paper:
    """A normalized arXiv paper record."""

    title: str
    authors: list[str]
    published: str  # ISO 8601 string, e.g. "2026-06-21T12:00:00Z"
    arxiv_id: str   # e.g. "2406.12345"
    abstract: str
    url: str        # canonical abs URL, e.g. "https://arxiv.org/abs/2406.12345"


@dataclass
class Summary:
    """LLM-generated Chinese summary for a paper."""

    chinese_abstract: str
    highlights: list[str] = field(default_factory=list)
    applications: list[str] = field(default_factory=list)
    error: str | None = None
```

- [ ] **Step 2: Verify import**

```bash
PYTHONPATH=src python -c "from paper_radar_bot.models import Paper, Summary; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add src/paper_radar_bot/models.py
git commit -m "feat(models): add Paper and Summary dataclasses"
```

---

### Task 3: Config Loader (`config.py`)

**Files:**
- Create: `src/paper_radar_bot/config.py`

**Interfaces:**
- Consumes: environment variables (loaded from `.env` if present)
- Produces: `Config(api_key: str, base_url: str, model: str, arxiv_query: str, arxiv_max_results: int, timezone: str, locale: str)` and `load_config() -> Config`

- [ ] **Step 1: Write `config.py`**

```python
"""Load and validate runtime configuration from environment variables."""

import os
import sys
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

_DEFAULTS = {
    "OPENAI_BASE_URL": "https://api.openai.com/v1",
    "OPENAI_MODEL": "gpt-4o-mini",
    "ARXIV_QUERY": "cat:cs.AI OR cat:cs.LG OR cat:cs.CL",
    "ARXIV_MAX_RESULTS": "10",
    "REPORT_TIMEZONE": "Asia/Shanghai",
    "REPORT_LOCALE": "zh_CN",
}


@dataclass
class Config:
    """Validated runtime configuration."""

    api_key: str
    base_url: str
    model: str
    arxiv_query: str
    arxiv_max_results: int
    timezone: str
    locale: str


def load_config() -> Config:
    """Load config from environment; exit with a clear message on failure."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY is not set. Copy .env.example to .env and fill in your key.", file=sys.stderr)
        sys.exit(1)

    raw_max = os.getenv("ARXIV_MAX_RESULTS", _DEFAULTS["ARXIV_MAX_RESULTS"])
    try:
        max_results = int(raw_max)
    except ValueError:
        print(f"ERROR: ARXIV_MAX_RESULTS must be an integer, got: {raw_max!r}", file=sys.stderr)
        sys.exit(1)

    return Config(
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL", _DEFAULTS["OPENAI_BASE_URL"]),
        model=os.getenv("OPENAI_MODEL", _DEFAULTS["OPENAI_MODEL"]),
        arxiv_query=os.getenv("ARXIV_QUERY", _DEFAULTS["ARXIV_QUERY"]),
        arxiv_max_results=max_results,
        timezone=os.getenv("REPORT_TIMEZONE", _DEFAULTS["REPORT_TIMEZONE"]),
        locale=os.getenv("REPORT_LOCALE", _DEFAULTS["REPORT_LOCALE"]),
    )
```

- [ ] **Step 2: Verify import**

```bash
PYTHONPATH=src python -c "from paper_radar_bot.config import load_config; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add src/paper_radar_bot/config.py
git commit -m "feat(config): add env-based config loader with validation"
```

---

### Task 4: arXiv Client with Unit Tests (`arxiv_client.py`)

**Files:**
- Create: `src/paper_radar_bot/arxiv_client.py`
- Create: `tests/test_arxiv_client.py`

**Interfaces:**
- Consumes: `Config` from Task 3; `Paper` from Task 2
- Produces: `fetch_papers(config: Config) -> list[Paper]`

- [ ] **Step 1: Write failing test**

```python
# tests/test_arxiv_client.py
"""Unit tests for arXiv Atom XML parsing (no HTTP calls)."""

import textwrap
from paper_radar_bot.arxiv_client import _parse_atom


SAMPLE_ATOM = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>Attention Is All You Need</title>
        <author><name>Ashish Vaswani</name></author>
        <author><name>Noam Shazeer</name></author>
        <published>2017-06-12T17:57:34Z</published>
        <id>http://arxiv.org/abs/1706.03762v5</id>
        <summary>The dominant sequence transduction models...</summary>
        <link href="http://arxiv.org/abs/1706.03762v5" rel="alternate" type="text/html"/>
      </entry>
    </feed>
""")


def test_parse_atom_returns_papers():
    papers = _parse_atom(SAMPLE_ATOM)
    assert len(papers) == 1


def test_parse_atom_title():
    papers = _parse_atom(SAMPLE_ATOM)
    assert papers[0].title == "Attention Is All You Need"


def test_parse_atom_authors():
    papers = _parse_atom(SAMPLE_ATOM)
    assert papers[0].authors == ["Ashish Vaswani", "Noam Shazeer"]


def test_parse_atom_published():
    papers = _parse_atom(SAMPLE_ATOM)
    assert papers[0].published == "2017-06-12T17:57:34Z"


def test_parse_atom_arxiv_id():
    papers = _parse_atom(SAMPLE_ATOM)
    assert papers[0].arxiv_id == "1706.03762"


def test_parse_atom_url():
    papers = _parse_atom(SAMPLE_ATOM)
    assert papers[0].url == "https://arxiv.org/abs/1706.03762"


def test_parse_atom_abstract():
    papers = _parse_atom(SAMPLE_ATOM)
    assert "dominant sequence transduction" in papers[0].abstract


def test_parse_atom_empty_feed():
    empty = '<feed xmlns="http://www.w3.org/2005/Atom"></feed>'
    assert _parse_atom(empty) == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
PYTHONPATH=src pytest tests/test_arxiv_client.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — `_parse_atom` not yet defined.

- [ ] **Step 3: Write `arxiv_client.py`**

```python
"""Fetch and parse arXiv Atom feeds into Paper records."""

import re
import sys
import xml.etree.ElementTree as ET

import requests

from paper_radar_bot.config import Config
from paper_radar_bot.models import Paper

_ATOM_NS = "http://www.w3.org/2005/Atom"
_ARXIV_API = "https://export.arxiv.org/api/query"
_ID_RE = re.compile(r"abs/([^v]+)")


def fetch_papers(config: Config) -> list[Paper]:
    """Query arXiv and return a list of Paper records."""
    params = {
        "search_query": config.arxiv_query,
        "max_results": config.arxiv_max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    try:
        response = requests.get(_ARXIV_API, params=params, timeout=30)
        response.raise_for_status()
    except requests.HTTPError as e:
        print(f"ERROR: arXiv request failed with status {e.response.status_code}: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as e:
        print(f"ERROR: arXiv request failed: {e}", file=sys.stderr)
        sys.exit(1)

    return _parse_atom(response.text)


def _parse_atom(xml_text: str) -> list[Paper]:
    """Parse an arXiv Atom XML string into Paper records."""
    root = ET.fromstring(xml_text)
    papers: list[Paper] = []

    for entry in root.findall(f"{{{_ATOM_NS}}}entry"):
        title_el = entry.find(f"{{{_ATOM_NS}}}title")
        title = title_el.text.strip() if title_el is not None and title_el.text else ""

        authors = [
            name_el.text.strip()
            for author in entry.findall(f"{{{_ATOM_NS}}}author")
            if (name_el := author.find(f"{{{_ATOM_NS}}}name")) is not None and name_el.text
        ]

        published_el = entry.find(f"{{{_ATOM_NS}}}published")
        published = published_el.text.strip() if published_el is not None and published_el.text else ""

        id_el = entry.find(f"{{{_ATOM_NS}}}id")
        raw_id = id_el.text.strip() if id_el is not None and id_el.text else ""
        match = _ID_RE.search(raw_id)
        arxiv_id = match.group(1) if match else raw_id

        summary_el = entry.find(f"{{{_ATOM_NS}}}summary")
        abstract = summary_el.text.strip() if summary_el is not None and summary_el.text else ""

        url = f"https://arxiv.org/abs/{arxiv_id}"

        papers.append(Paper(
            title=title,
            authors=authors,
            published=published,
            arxiv_id=arxiv_id,
            abstract=abstract,
            url=url,
        ))

    return papers
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
PYTHONPATH=src pytest tests/test_arxiv_client.py -v
```

Expected: all 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/paper_radar_bot/arxiv_client.py tests/test_arxiv_client.py
git commit -m "feat(arxiv_client): add Atom feed fetcher and parser with unit tests"
```

---

### Task 5: Summarizer (`summarizer.py`)

**Files:**
- Create: `src/paper_radar_bot/summarizer.py`

**Interfaces:**
- Consumes: `Config` from Task 3; `Paper` from Task 2
- Produces: `summarize(paper: Paper, config: Config) -> Summary`

- [ ] **Step 1: Write `summarizer.py`**

```python
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
    except (OpenAIError, json.JSONDecodeError, KeyError) as e:
        logger.warning("Summarization failed for paper %r: %s", paper.arxiv_id, e)
        return Summary(
            chinese_abstract="",
            highlights=[],
            applications=[],
            error=str(e),
        )
```

- [ ] **Step 2: Verify import**

```bash
PYTHONPATH=src python -c "from paper_radar_bot.summarizer import summarize; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add src/paper_radar_bot/summarizer.py
git commit -m "feat(summarizer): add OpenAI-compatible chat completions summarizer"
```

---

### Task 6: Markdown Renderer with Unit Tests (`renderer.py`)

**Files:**
- Create: `src/paper_radar_bot/renderer.py`
- Create: `tests/test_renderer.py`

**Interfaces:**
- Consumes: `Paper` and `Summary` from Task 2; `date_str: str` (e.g. `"2026-06-21"`)
- Produces:
  - `render_report(papers: list[Paper], summaries: list[Summary], query: str, date_str: str) -> str`
  - `render_paper_section(paper: Paper, summary: Summary) -> str`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_renderer.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
PYTHONPATH=src pytest tests/test_renderer.py -v
```

Expected: `ImportError` — `renderer` module does not exist yet.

- [ ] **Step 3: Write `renderer.py`**

```python
"""Render Paper records and Summaries into a Markdown report string."""

from paper_radar_bot.models import Paper, Summary


def render_paper_section(paper: Paper, summary: Summary) -> str:
    """Render a single paper and its summary as a Markdown section."""
    authors_str = "、".join(paper.authors) if paper.authors else "未知作者"
    published_date = paper.published[:10] if len(paper.published) >= 10 else paper.published

    lines = [
        f"## {paper.title}",
        "",
        f"- **作者：** {authors_str}",
        f"- **发布时间：** {published_date}",
        f"- **arXiv 链接：** [{paper.url}]({paper.url})",
        "",
    ]

    if summary.error is not None:
        lines += [
            "### 中文总结",
            "",
            f"> 总结失败：{summary.error}",
            "",
        ]
    else:
        lines += [
            "### 中文总结",
            "",
            summary.chinese_abstract,
            "",
        ]

        if summary.highlights:
            lines += ["**关键亮点：**", ""]
            for h in summary.highlights:
                lines.append(f"- {h}")
            lines.append("")

        if summary.applications:
            lines += ["**潜在应用方向：**", ""]
            for a in summary.applications:
                lines.append(f"- {a}")
            lines.append("")

    return "\n".join(lines)


def render_report(
    papers: list[Paper],
    summaries: list[Summary],
    query: str,
    date_str: str,
) -> str:
    """Render all papers into a complete Markdown report."""
    header = "\n".join([
        f"# Paper Radar 日报 — {date_str}",
        "",
        "## 运行元信息",
        "",
        f"- **运行日期：** {date_str}",
        f"- **检索主题：** `{query}`",
        f"- **论文数量：** {len(papers)}",
        "",
        "---",
        "",
    ])

    sections = [render_paper_section(p, s) for p, s in zip(papers, summaries)]
    return header + "\n---\n\n".join(sections)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
PYTHONPATH=src pytest tests/test_renderer.py -v
```

Expected: all 10 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/paper_radar_bot/renderer.py tests/test_renderer.py
git commit -m "feat(renderer): add Markdown renderer with unit tests"
```

---

### Task 7: Report Writer with Unit Tests (`writer.py`)

**Files:**
- Create: `src/paper_radar_bot/writer.py`
- Create: `tests/test_writer.py`

**Interfaces:**
- Consumes: `report_content: str`, `date_str: str`, `reports_dir: str` (default `"reports"`)
- Produces: `write_report(content: str, date_str: str, reports_dir: str = "reports") -> str` (returns written file path)

- [ ] **Step 1: Write failing tests**

```python
# tests/test_writer.py
"""Unit tests for report file writing."""

import os
import tempfile

from paper_radar_bot.writer import write_report


def test_write_report_creates_file():
    with tempfile.TemporaryDirectory() as tmp:
        path = write_report("# Hello", "2026-06-21", reports_dir=tmp)
        assert os.path.isfile(path)


def test_write_report_correct_filename():
    with tempfile.TemporaryDirectory() as tmp:
        path = write_report("# Hello", "2026-06-21", reports_dir=tmp)
        assert os.path.basename(path) == "2026-06-21.md"


def test_write_report_file_content():
    with tempfile.TemporaryDirectory() as tmp:
        path = write_report("# Hello World", "2026-06-21", reports_dir=tmp)
        with open(path, encoding="utf-8") as f:
            assert f.read() == "# Hello World"


def test_write_report_creates_dir_if_missing():
    with tempfile.TemporaryDirectory() as tmp:
        subdir = os.path.join(tmp, "new_subdir")
        path = write_report("content", "2026-06-21", reports_dir=subdir)
        assert os.path.isfile(path)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
PYTHONPATH=src pytest tests/test_writer.py -v
```

Expected: `ImportError` — `writer` module does not exist yet.

- [ ] **Step 3: Write `writer.py`**

```python
"""Create the reports directory and persist the Markdown report to disk."""

import os
import sys


def write_report(content: str, date_str: str, reports_dir: str = "reports") -> str:
    """Write content to reports/<date_str>.md; return the file path."""
    try:
        os.makedirs(reports_dir, exist_ok=True)
    except OSError as e:
        print(f"ERROR: Cannot create reports directory {reports_dir!r}: {e}", file=sys.stderr)
        sys.exit(1)

    file_path = os.path.join(reports_dir, f"{date_str}.md")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as e:
        print(f"ERROR: Cannot write report to {file_path!r}: {e}", file=sys.stderr)
        sys.exit(1)

    return file_path
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
PYTHONPATH=src pytest tests/test_writer.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/paper_radar_bot/writer.py tests/test_writer.py
git commit -m "feat(writer): add report file writer with unit tests"
```

---

### Task 8: Main Orchestrator (`main.py`)

**Files:**
- Create: `src/paper_radar_bot/main.py`

**Interfaces:**
- Consumes: all modules from Tasks 3–7
- Produces: `main()` entry point; `reports/<YYYY-MM-DD>.md` file on disk

- [ ] **Step 1: Write `main.py`**

```python
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
```

- [ ] **Step 2: Verify full import chain**

```bash
PYTHONPATH=src python -c "from paper_radar_bot.main import main; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Run all tests to confirm nothing is broken**

```bash
PYTHONPATH=src pytest tests/ -v
```

Expected: all 22 tests PASS (8 arxiv + 10 renderer + 4 writer).

- [ ] **Step 4: Commit**

```bash
git add src/paper_radar_bot/main.py
git commit -m "feat(main): add orchestration entry point"
```

---

### Task 9: Windows Launcher & README

**Files:**
- Create: `run_paper_radar.bat`
- Create: `README.md`

**Interfaces:**
- Consumes: `src/paper_radar_bot/main.py`; `.env`
- Produces: double-clickable launcher for Windows users; project documentation

- [ ] **Step 1: Write `run_paper_radar.bat`**

```bat
@echo off
setlocal

:: Change to the directory containing this .bat file
cd /d "%~dp0"

:: Activate virtualenv if present
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

:: Run the bot
python -m paper_radar_bot.main
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: paper_radar_bot exited with code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Done. Check the reports\ folder.
pause
```

- [ ] **Step 2: Write `README.md`**

```markdown
# Paper Radar Bot

Fetches recent arXiv papers by topic, generates Chinese summaries via an OpenAI-compatible model, and saves a dated Markdown report to `reports/`.

## Quick Start (Windows)

1. Install Python 3.11+
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in `OPENAI_API_KEY`
4. Double-click `run_paper_radar.bat`

The report is saved to `reports/YYYY-MM-DD.md`.

## Quick Start (Linux / macOS / GitHub Actions)

```bash
pip install -r requirements.txt
cp .env.example .env  # then fill in OPENAI_API_KEY
PYTHONPATH=src python -m paper_radar_bot.main
```

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | Your OpenAI-compatible API key |
| `OPENAI_BASE_URL` | No | `https://api.openai.com/v1` | API base URL |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | Model name |
| `ARXIV_QUERY` | No | `cat:cs.AI OR cat:cs.LG OR cat:cs.CL` | arXiv search query |
| `ARXIV_MAX_RESULTS` | No | `10` | Max papers per run |
| `REPORT_TIMEZONE` | No | `Asia/Shanghai` | Timezone label (informational) |
| `REPORT_LOCALE` | No | `zh_CN` | Locale label (informational) |

## Running Tests

```bash
PYTHONPATH=src pytest tests/ -v
```
```

- [ ] **Step 3: Commit**

```bash
git add run_paper_radar.bat README.md
git commit -m "chore(docs): add Windows bat launcher and README"
```

---

### Task 10: GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/paper_radar.yml`

**Interfaces:**
- Consumes: `OPENAI_API_KEY` from GitHub repository secrets
- Produces: scheduled workflow that runs the bot, commits the report, and pushes to `main`

- [ ] **Step 1: Create workflow directory**

```bash
mkdir -p .github/workflows
```

- [ ] **Step 2: Write `.github/workflows/paper_radar.yml`**

```yaml
name: Paper Radar Bot

on:
  schedule:
    # Run at 08:00 UTC every day (Asia/Shanghai 16:00)
    - cron: "0 8 * * *"
  workflow_dispatch:  # Allow manual trigger from GitHub UI

jobs:
  run-bot:
    runs-on: ubuntu-latest

    permissions:
      contents: write  # needed to push the report

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run paper radar bot
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          OPENAI_BASE_URL: ${{ vars.OPENAI_BASE_URL || 'https://api.openai.com/v1' }}
          OPENAI_MODEL: ${{ vars.OPENAI_MODEL || 'gpt-4o-mini' }}
          ARXIV_QUERY: ${{ vars.ARXIV_QUERY || 'cat:cs.AI OR cat:cs.LG OR cat:cs.CL' }}
          ARXIV_MAX_RESULTS: ${{ vars.ARXIV_MAX_RESULTS || '10' }}
          PYTHONPATH: src
        run: python -m paper_radar_bot.main

      - name: Commit and push report
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add reports/
          git diff --cached --quiet || git commit -m "chore(reports): add daily paper radar report"
          git push
```

- [ ] **Step 3: Verify YAML syntax**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/paper_radar.yml'))"
```

Expected: no output (valid YAML).

- [ ] **Step 4: Run full test suite one final time**

```bash
PYTHONPATH=src pytest tests/ -v
```

Expected: all 22 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/paper_radar.yml
git commit -m "chore(ci): add GitHub Actions workflow for scheduled paper radar"
```

---

## Acceptance Checklist (from spec)

- [ ] User can copy `.env.example` to `.env` and fill in `OPENAI_API_KEY`
- [ ] User can run `run_paper_radar.bat` on Windows
- [ ] Report is generated under `reports/YYYY-MM-DD.md`
- [ ] Report contains paper metadata and Chinese summaries
- [ ] GitHub Actions workflow exists for scheduled execution and auto-commit
- [ ] Unit tests for parsing, rendering, and writing pass locally (`pytest tests/ -v`)
