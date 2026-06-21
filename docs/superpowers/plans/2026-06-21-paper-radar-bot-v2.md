# Paper Radar Bot v2 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 paper_radar_bot 添加多领域 YAML 配置、HTML 默认输出格式，并将文档改写为中文。

**Architecture:** 新增 `Topic`/`TopicResult` 数据类、`topics.py` YAML 加载器和 `html_renderer.py` 独立渲染器；修改 `renderer.py`/`writer.py`/`main.py` 适配多领域接口；`arxiv_client.fetch_papers` 签名从 `Config` 改为 `(query, max_results)` 以解耦。

**Tech Stack:** Python 3.11+, pyyaml 6.0.2, 现有 requests/openai/python-dotenv/pytest

## Global Constraints

- Python ≥ 3.11（使用 `list[str]`、`str | None`，不用 typing 模块）
- 所有源码在 `src/paper_radar_bot/`；测试在 `tests/`
- 公开函数/方法必须有类型注解和 docstring
- 禁止 `from module import *`；每个 import 单独一行
- 行长 ≤ 120 字符
- `snake_case` 函数/变量，`PascalCase` 类，`UPPER_SNAKE_CASE` 常量
- f-string 优先；`None` 比较用 `is`/`is not`
- 禁止裸 `except:`；必须捕获具体异常
- 提交格式：`<type>(<scope>): <subject>`
- 所有 python/pytest 命令使用 `PYTHONPATH=src`

---

## 文件变更映射

| 操作 | 文件 | 说明 |
|------|------|------|
| 新增 | `src/paper_radar_bot/topics.py` | 加载 topics.yaml → `list[Topic]` |
| 新增 | `src/paper_radar_bot/html_renderer.py` | HTML 渲染，单文件内嵌 CSS |
| 新增 | `tests/test_topics.py` | topics.py 单元测试 |
| 新增 | `tests/test_html_renderer.py` | html_renderer.py 单元测试 |
| 新增 | `topics.yaml` | 默认领域配置（三个领域） |
| 修改 | `src/paper_radar_bot/models.py` | 新增 `Topic`、`TopicResult` 数据类 |
| 修改 | `src/paper_radar_bot/config.py` | 新增 `output_format` 字段 |
| 修改 | `src/paper_radar_bot/arxiv_client.py` | `fetch_papers(query, max_results)` 去除 Config 依赖 |
| 修改 | `src/paper_radar_bot/renderer.py` | `render_report` 改为接受 `list[TopicResult]` |
| 修改 | `src/paper_radar_bot/writer.py` | `write_report` 新增 `output_format` 参数 |
| 修改 | `src/paper_radar_bot/main.py` | 多领域循环 + 按格式分发渲染 |
| 修改 | `tests/test_renderer.py` | 适配新 `render_report` 签名 |
| 修改 | `tests/test_writer.py` | 适配新 `write_report` 签名 |
| 修改 | `requirements.txt` | 新增 `pyyaml==6.0.2` |
| 修改 | `README.md` | 改写为中文 |
| 修改 | `.env.example` | 新增 `OUTPUT_FORMAT` |

---

### Task 1: Topic 数据类 + topics.py + 单元测试

**Files:**
- Modify: `src/paper_radar_bot/models.py`
- Create: `src/paper_radar_bot/topics.py`
- Modify: `requirements.txt`
- Create: `tests/test_topics.py`

**Interfaces:**
- Produces:
  - `Topic(name: str, keywords: list[str], max_results: int = 10)` — `.arxiv_query: str` 属性
  - `TopicResult(topic: Topic, papers: list[Paper], summaries: list[Summary])`
  - `load_topics(topics_file: str = "topics.yaml", fallback_query: str | None = None) -> list[Topic]`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_topics.py
"""Unit tests for topic loading and query construction."""

import os
import tempfile

from paper_radar_bot.models import Topic
from paper_radar_bot.topics import load_topics


def test_topic_arxiv_query_single_keyword():
    topic = Topic(name="Test", keywords=["LLM translation"])
    assert topic.arxiv_query == 'all:"LLM translation"'


def test_topic_arxiv_query_multiple_keywords():
    topic = Topic(name="Test", keywords=["LLM translation", "neural machine translation"])
    assert topic.arxiv_query == 'all:"LLM translation" OR all:"neural machine translation"'


def test_load_topics_from_yaml():
    yaml_content = (
        "topics:\n"
        "  - name: AI Test\n"
        "    keywords:\n"
        "      - artificial intelligence\n"
        "      - machine learning\n"
        "    max_results: 5\n"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write(yaml_content)
        path = f.name
    try:
        topics = load_topics(path)
        assert len(topics) == 1
        assert topics[0].name == "AI Test"
        assert topics[0].keywords == ["artificial intelligence", "machine learning"]
        assert topics[0].max_results == 5
    finally:
        os.unlink(path)


def test_load_topics_file_not_found_uses_fallback_query():
    topics = load_topics("nonexistent_xyz.yaml", fallback_query="cat:cs.AI")
    assert len(topics) == 1
    assert topics[0].keywords == ["cat:cs.AI"]


def test_load_topics_file_not_found_uses_defaults():
    topics = load_topics("nonexistent_xyz.yaml")
    assert len(topics) == 3
    assert all(isinstance(t, Topic) for t in topics)


def test_load_topics_skips_empty_keywords():
    yaml_content = (
        "topics:\n"
        "  - name: Valid\n"
        "    keywords:\n"
        "      - artificial intelligence\n"
        "  - name: Empty\n"
        "    keywords: []\n"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write(yaml_content)
        path = f.name
    try:
        topics = load_topics(path)
        assert len(topics) == 1
        assert topics[0].name == "Valid"
    finally:
        os.unlink(path)
```

- [ ] **Step 2: 运行测试确认失败**

```bash
PYTHONPATH=src pytest tests/test_topics.py -v
```

期望：`ImportError` 或 `ModuleNotFoundError`。

- [ ] **Step 3: 在 `requirements.txt` 添加 pyyaml**

将文件改为：

```
requests==2.32.3
python-dotenv==1.0.1
openai>=1.52.0
pyyaml==6.0.2
pytest==8.2.2
```

安装：

```bash
pip install pyyaml==6.0.2
```

- [ ] **Step 4: 在 `models.py` 末尾追加 `Topic` 和 `TopicResult`**

在文件末尾（`Summary` 数据类之后）追加：

```python

@dataclass
class Topic:
    """单个领域的配置。"""

    name: str
    keywords: list[str]
    max_results: int = 10

    @property
    def arxiv_query(self) -> str:
        """将关键词列表 OR 拼接为 arXiv 查询串。"""
        return " OR ".join(f'all:"{kw}"' for kw in self.keywords)


@dataclass
class TopicResult:
    """单个领域的抓取与总结结果。"""

    topic: Topic
    papers: list["Paper"]
    summaries: list["Summary"]
```

注意：`Paper` 和 `Summary` 已在同文件定义，直接引用即可（无需字符串前向引用），只需确保顺序正确——`Topic` 和 `TopicResult` 追加在 `Paper`/`Summary` 之后。

完整 `models.py` 内容：

```python
"""Shared data structures for paper records and summaries."""

from dataclasses import dataclass, field


@dataclass
class Paper:
    """A normalized arXiv paper record."""

    title: str
    authors: list[str]
    published: str
    arxiv_id: str
    abstract: str
    url: str


@dataclass
class Summary:
    """LLM-generated Chinese summary for a paper."""

    chinese_abstract: str
    highlights: list[str] = field(default_factory=list)
    applications: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class Topic:
    """单个领域的配置。"""

    name: str
    keywords: list[str]
    max_results: int = 10

    @property
    def arxiv_query(self) -> str:
        """将关键词列表 OR 拼接为 arXiv 查询串。"""
        return " OR ".join(f'all:"{kw}"' for kw in self.keywords)


@dataclass
class TopicResult:
    """单个领域的抓取与总结结果。"""

    topic: Topic
    papers: list[Paper]
    summaries: list[Summary]
```

- [ ] **Step 5: 创建 `src/paper_radar_bot/topics.py`**

```python
"""Load and parse topics.yaml into Topic records."""

import sys
from pathlib import Path

import yaml

from paper_radar_bot.models import Topic

_DEFAULT_TOPICS: list[Topic] = [
    Topic(
        name="LLM Translation",
        keywords=["LLM translation", "large language model translation", "neural machine translation"],
        max_results=10,
    ),
    Topic(
        name="Omni Model",
        keywords=["omni model", "multimodal model", "vision language model", "unified model"],
        max_results=10,
    ),
    Topic(
        name="Sign Language Translation",
        keywords=[
            "sign language translation",
            "sign language recognition",
            "gesture recognition",
            "sign language production",
        ],
        max_results=10,
    ),
]


def load_topics(topics_file: str = "topics.yaml", fallback_query: str | None = None) -> list[Topic]:
    """Load topics from YAML; fall back to fallback_query or built-in defaults if file is absent."""
    path = Path(topics_file)
    if not path.exists():
        if fallback_query is not None:
            return [Topic(name="默认领域", keywords=[fallback_query], max_results=10)]
        return list(_DEFAULT_TOPICS)

    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"ERROR: Failed to parse {topics_file}: {e}", file=sys.stderr)
        sys.exit(1)

    topics: list[Topic] = []
    for item in data.get("topics", []):
        keywords: list[str] = item.get("keywords", [])
        if not keywords:
            print(f"WARNING: Topic {item.get('name', '?')!r} has no keywords, skipping.", file=sys.stderr)
            continue
        topics.append(Topic(
            name=item["name"],
            keywords=keywords,
            max_results=item.get("max_results", 10),
        ))

    if not topics:
        print(f"WARNING: No valid topics found in {topics_file}, using built-in defaults.", file=sys.stderr)
        return list(_DEFAULT_TOPICS)

    return topics
```

- [ ] **Step 6: 运行测试确认通过**

```bash
PYTHONPATH=src pytest tests/test_topics.py -v
```

期望：6 个测试全部 PASS。

- [ ] **Step 7: 提交**

```bash
git add src/paper_radar_bot/models.py src/paper_radar_bot/topics.py tests/test_topics.py requirements.txt
git commit -m "feat(topics): add Topic/TopicResult dataclasses and YAML topic loader"
```

---

### Task 2: config.py 新增 output_format + .env.example 更新

**Files:**
- Modify: `src/paper_radar_bot/config.py`
- Modify: `.env.example`

**Interfaces:**
- Consumes: 环境变量 `OUTPUT_FORMAT`（`"html"` 或 `"markdown"`）
- Produces: `Config.output_format: str`

- [ ] **Step 1: 修改 `config.py`**

完整文件内容：

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
    "ARXIV_QUERY": "cat:cs.AI",
    "ARXIV_MAX_RESULTS": "10",
    "REPORT_TIMEZONE": "Asia/Shanghai",
    "REPORT_LOCALE": "zh_CN",
    "OUTPUT_FORMAT": "html",
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
    output_format: str  # "html" or "markdown"


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

    raw_format = os.getenv("OUTPUT_FORMAT", _DEFAULTS["OUTPUT_FORMAT"]).lower()
    if raw_format not in ("html", "markdown"):
        print(f"ERROR: OUTPUT_FORMAT must be 'html' or 'markdown', got: {raw_format!r}", file=sys.stderr)
        sys.exit(1)

    return Config(
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL", _DEFAULTS["OPENAI_BASE_URL"]),
        model=os.getenv("OPENAI_MODEL", _DEFAULTS["OPENAI_MODEL"]),
        arxiv_query=os.getenv("ARXIV_QUERY", _DEFAULTS["ARXIV_QUERY"]),
        arxiv_max_results=max_results,
        timezone=os.getenv("REPORT_TIMEZONE", _DEFAULTS["REPORT_TIMEZONE"]),
        locale=os.getenv("REPORT_LOCALE", _DEFAULTS["REPORT_LOCALE"]),
        output_format=raw_format,
    )
```

- [ ] **Step 2: 更新 `.env.example`**

完整内容：

```dotenv
# 必填
OPENAI_API_KEY=sk-...

# 可选 — 括号内为默认值
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
ARXIV_QUERY=cat:cs.AI
ARXIV_MAX_RESULTS=10
OUTPUT_FORMAT=html
REPORT_TIMEZONE=Asia/Shanghai
REPORT_LOCALE=zh_CN
```

- [ ] **Step 3: 验证导入**

```bash
PYTHONPATH=src python -c "from paper_radar_bot.config import load_config; print('ok')"
```

期望：`ok`

- [ ] **Step 4: 提交**

```bash
git add src/paper_radar_bot/config.py .env.example
git commit -m "feat(config): add output_format field with html/markdown validation"
```

---

### Task 3: HTML 渲染器 + 单元测试

**Files:**
- Create: `src/paper_radar_bot/html_renderer.py`
- Create: `tests/test_html_renderer.py`

**Interfaces:**
- Consumes: `TopicResult(topic: Topic, papers: list[Paper], summaries: list[Summary])` from Task 1
- Produces: `render_report(results: list[TopicResult], date_str: str) -> str`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_html_renderer.py
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
```

- [ ] **Step 2: 运行测试确认失败**

```bash
PYTHONPATH=src pytest tests/test_html_renderer.py -v
```

期望：`ImportError`。

- [ ] **Step 3: 创建 `src/paper_radar_bot/html_renderer.py`**

```python
"""Render multi-topic paper results into a single-file offline HTML report."""

from paper_radar_bot.models import Paper, Summary, TopicResult

_CSS = """\
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: system-ui, -apple-system, sans-serif;
    font-size: 16px; line-height: 1.6; color: #24292e;
    max-width: 860px; margin: 0 auto; padding: 24px 16px;
}
h1 { font-size: 24px; font-weight: 600; margin-bottom: 8px; }
h2 {
    font-size: 20px; font-weight: 600; color: #0366d6;
    border-bottom: 1px solid #e1e4e8; padding-bottom: 6px; margin: 32px 0 16px;
}
h3 { font-size: 16px; font-weight: 600; margin-bottom: 4px; }
.meta { color: #6a737d; font-size: 14px; margin-bottom: 16px; }
nav { margin: 16px 0; font-size: 14px; }
nav a { color: #0366d6; text-decoration: none; margin-right: 4px; }
nav a:hover { text-decoration: underline; }
nav span.sep { color: #6a737d; margin-right: 4px; }
.paper { border: 1px solid #e1e4e8; border-radius: 4px; padding: 16px; margin-bottom: 16px; }
.paper-meta { color: #6a737d; font-size: 14px; margin-bottom: 8px; }
.paper-meta a { color: #0366d6; text-decoration: none; }
.paper-meta a:hover { text-decoration: underline; }
.abstract { margin-bottom: 12px; }
.section-label { font-weight: 600; margin: 8px 0 4px; }
ul { padding-left: 20px; margin-bottom: 8px; }
li { margin-bottom: 2px; }
.error { background: #f6f8fa; color: #6a737d; font-style: italic; padding: 8px; border-radius: 4px; }
hr { border: none; border-top: 1px solid #e1e4e8; margin: 24px 0; }
.topic-count { font-size: 14px; font-weight: normal; color: #6a737d; }
"""


def _e(text: str) -> str:
    """Escape HTML special characters."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _section_id(name: str) -> str:
    """Convert a topic name to a safe HTML id."""
    return "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")


def _render_paper(paper: Paper, summary: Summary) -> str:
    """Render a single paper as an HTML article."""
    authors_str = "、".join(paper.authors) if paper.authors else "未知作者"
    published_date = paper.published[:10] if len(paper.published) >= 10 else paper.published

    if summary.error is not None:
        body = f'<p class="error">总结失败：{_e(summary.error)}</p>'
    else:
        highlights_html = ""
        if summary.highlights:
            items = "".join(f"<li>{_e(h)}</li>" for h in summary.highlights)
            highlights_html = f'<p class="section-label">关键亮点：</p><ul>{items}</ul>'
        applications_html = ""
        if summary.applications:
            items = "".join(f"<li>{_e(a)}</li>" for a in summary.applications)
            applications_html = f'<p class="section-label">潜在应用方向：</p><ul>{items}</ul>'
        body = f'<p class="abstract">{_e(summary.chinese_abstract)}</p>{highlights_html}{applications_html}'

    return (
        f'<article class="paper">'
        f'<h3>{_e(paper.title)}</h3>'
        f'<p class="paper-meta">{_e(authors_str)} · {_e(published_date)} · '
        f'<a href="{_e(paper.url)}" target="_blank">arXiv</a></p>'
        f'{body}'
        f'</article>'
    )


def render_report(results: list[TopicResult], date_str: str) -> str:
    """Render all topic results into a complete single-file HTML report."""
    total_papers = sum(len(r.papers) for r in results)

    nav_parts = []
    for i, r in enumerate(results):
        if i > 0:
            nav_parts.append('<span class="sep">|</span>')
        nav_parts.append(f'<a href="#{_section_id(r.topic.name)}">{_e(r.topic.name)}</a>')
    nav_html = "".join(nav_parts)

    sections = []
    for r in results:
        sid = _section_id(r.topic.name)
        papers_html = "".join(_render_paper(p, s) for p, s in zip(r.papers, r.summaries))
        sections.append(
            f'<section id="{sid}">'
            f'<h2>{_e(r.topic.name)} '
            f'<span class="topic-count">（{len(r.papers)} 篇）</span></h2>'
            f'{papers_html}'
            f'</section>'
        )

    body = "\n".join(sections)

    return (
        f'<!DOCTYPE html>\n'
        f'<html lang="zh-CN">\n'
        f'<head>\n'
        f'<meta charset="UTF-8">\n'
        f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>Paper Radar 日报 — {_e(date_str)}</title>\n'
        f'<style>{_CSS}</style>\n'
        f'</head>\n'
        f'<body>\n'
        f'<h1>Paper Radar 日报 — {_e(date_str)}</h1>\n'
        f'<p class="meta">运行日期：{_e(date_str)} · 领域数：{len(results)} · 论文总数：{total_papers}</p>\n'
        f'<nav>{nav_html}</nav>\n'
        f'<hr>\n'
        f'{body}\n'
        f'</body>\n'
        f'</html>'
    )
```

- [ ] **Step 4: 运行测试确认通过**

```bash
PYTHONPATH=src pytest tests/test_html_renderer.py -v
```

期望：7 个测试全部 PASS。

- [ ] **Step 5: 提交**

```bash
git add src/paper_radar_bot/html_renderer.py tests/test_html_renderer.py
git commit -m "feat(html_renderer): add single-file HTML report renderer with inline CSS"
```

---

### Task 4: renderer.py 适配多领域 + test_renderer.py 更新

**Files:**
- Modify: `src/paper_radar_bot/renderer.py`
- Modify: `tests/test_renderer.py`

**Interfaces:**
- Consumes: `TopicResult` from Task 1
- Produces: `render_report(results: list[TopicResult], date_str: str) -> str`（签名变更）
- 保留: `render_paper_section(paper: Paper, summary: Summary) -> str`（签名不变）

- [ ] **Step 1: 先更新 `tests/test_renderer.py`（令其失败）**

完整替换为：

```python
"""Unit tests for Markdown rendering."""

from paper_radar_bot.models import Paper, Summary, Topic, TopicResult
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

_TOPIC = Topic(name="Test Topic", keywords=["test"], max_results=5)
_RESULT = TopicResult(topic=_TOPIC, papers=[_PAPER], summaries=[_SUMMARY])


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
    report = render_report([_RESULT], date_str="2026-06-21")
    assert "2026-06-21" in report


def test_render_report_contains_topic_name():
    report = render_report([_RESULT], date_str="2026-06-21")
    assert "Test Topic" in report


def test_render_report_contains_paper_count():
    report = render_report([_RESULT], date_str="2026-06-21")
    assert "1" in report
```

- [ ] **Step 2: 运行测试确认失败**

```bash
PYTHONPATH=src pytest tests/test_renderer.py -v
```

期望：`test_render_report_*` 的 3 个测试 FAIL（旧签名不匹配）。

- [ ] **Step 3: 更新 `renderer.py`**

完整替换为：

```python
"""Render Paper records and Summaries into a Markdown report string."""

from paper_radar_bot.models import Paper, Summary, TopicResult


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


def render_report(results: list[TopicResult], date_str: str) -> str:
    """Render all topic results into a complete Markdown report."""
    total_papers = sum(len(r.papers) for r in results)

    header_lines = [
        f"# Paper Radar 日报 — {date_str}",
        "",
        "## 运行元信息",
        "",
        f"- **运行日期：** {date_str}",
        f"- **领域数量：** {len(results)}",
        f"- **论文总数：** {total_papers}",
        "",
        "---",
        "",
    ]

    topic_sections = []
    for result in results:
        paper_sections = [
            render_paper_section(p, s)
            for p, s in zip(result.papers, result.summaries)
        ]
        topic_header = f"# {result.topic.name}（{len(result.papers)} 篇）\n\n"
        topic_sections.append(topic_header + "\n---\n\n".join(paper_sections))

    return "\n".join(header_lines) + "\n\n---\n\n".join(topic_sections)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
PYTHONPATH=src pytest tests/test_renderer.py -v
```

期望：10 个测试全部 PASS。

- [ ] **Step 5: 提交**

```bash
git add src/paper_radar_bot/renderer.py tests/test_renderer.py
git commit -m "refactor(renderer): update render_report to accept list[TopicResult]"
```

---

### Task 5: writer.py 支持 output_format + test_writer.py 更新

**Files:**
- Modify: `src/paper_radar_bot/writer.py`
- Modify: `tests/test_writer.py`

**Interfaces:**
- Produces: `write_report(content: str, date_str: str, output_format: str = "html", reports_dir: str = "reports") -> str`

- [ ] **Step 1: 先更新 `tests/test_writer.py`（令其失败）**

完整替换为：

```python
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
```

- [ ] **Step 2: 运行测试确认失败**

```bash
PYTHONPATH=src pytest tests/test_writer.py -v
```

期望：传入 `output_format` 关键字参数时报 `TypeError`（旧签名不接受该参数）。

- [ ] **Step 3: 更新 `writer.py`**

完整替换为：

```python
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
```

- [ ] **Step 4: 运行测试确认通过**

```bash
PYTHONPATH=src pytest tests/test_writer.py -v
```

期望：5 个测试全部 PASS。

- [ ] **Step 5: 提交**

```bash
git add src/paper_radar_bot/writer.py tests/test_writer.py
git commit -m "feat(writer): support output_format parameter for html/markdown extension"
```

---

### Task 6: arxiv_client 签名更新 + main.py 多领域重写

**Files:**
- Modify: `src/paper_radar_bot/arxiv_client.py`
- Modify: `src/paper_radar_bot/main.py`

**Interfaces:**
- Consumes: `Topic.arxiv_query: str`、`Topic.max_results: int`、`load_topics()`、`render_report`（html/md）、`write_report(..., output_format=...)`
- Produces: `fetch_papers(query: str, max_results: int) -> list[Paper]`（去除 Config 依赖）

- [ ] **Step 1: 更新 `arxiv_client.py` — 移除 Config 依赖**

修改 `fetch_papers` 函数签名，移除 `from paper_radar_bot.config import Config` 导入：

```python
"""Fetch and parse arXiv Atom feeds into Paper records."""

import re
import sys
import xml.etree.ElementTree as ET

import requests

from paper_radar_bot.models import Paper

_ATOM_NS = "http://www.w3.org/2005/Atom"
_ARXIV_API = "https://export.arxiv.org/api/query"
_ID_RE = re.compile(r"abs/([^v]+)")
_HEADERS = {"User-Agent": "paper_radar_bot/0.1 (https://github.com/geekchen007/paper_radar_bot)"}


def fetch_papers(query: str, max_results: int) -> list[Paper]:
    """Query arXiv with the given query string and return a list of Paper records."""
    params = {
        "search_query": query,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    try:
        response = requests.get(_ARXIV_API, params=params, headers=_HEADERS, timeout=60)
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

- [ ] **Step 2: 验证现有 arxiv 单元测试仍通过**

```bash
PYTHONPATH=src pytest tests/test_arxiv_client.py -v
```

期望：8 个测试全部 PASS（`_parse_atom` 签名未变）。

- [ ] **Step 3: 重写 `main.py`**

```python
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
```

- [ ] **Step 4: 运行全量测试**

```bash
PYTHONPATH=src pytest tests/ -v
```

期望：所有测试（8 + 10 + 5 + 7 + 6 = 36 个）全部 PASS。

- [ ] **Step 5: 提交**

```bash
git add src/paper_radar_bot/arxiv_client.py src/paper_radar_bot/main.py
git commit -m "refactor(main): multi-topic loop with html/markdown format dispatch; decouple fetch_papers from Config"
```

---

### Task 7: topics.yaml 默认文件 + README 中文重写

**Files:**
- Create: `topics.yaml`
- Modify: `README.md`

**Interfaces:**
- 无代码接口；为用户提供可直接编辑的配置和文档

- [ ] **Step 1: 创建 `topics.yaml`**

```yaml
# Paper Radar Bot — 领域配置
# 每个 topic 支持多个关键词，查询时自动 OR 合并。
# 修改此文件后重新运行即可生效，无需修改代码。

topics:
  - name: LLM Translation
    keywords:
      - LLM translation
      - large language model translation
      - neural machine translation
    max_results: 10

  - name: Omni Model
    keywords:
      - omni model
      - multimodal model
      - vision language model
      - unified model
    max_results: 10

  - name: Sign Language Translation
    keywords:
      - sign language translation
      - sign language recognition
      - gesture recognition
      - sign language production
    max_results: 10
```

- [ ] **Step 2: 验证 topics.yaml 可正常加载**

```bash
PYTHONPATH=src python -c "
from paper_radar_bot.topics import load_topics
topics = load_topics()
for t in topics:
    print(t.name, '->', t.arxiv_query[:60])
"
```

期望输出（每行一个领域名和截断的查询串）：

```
LLM Translation -> all:"LLM translation" OR all:"large language mo
Omni Model -> all:"omni model" OR all:"multimodal model" OR all:"vi
Sign Language Translation -> all:"sign language translation" OR all
```

- [ ] **Step 3: 重写 `README.md` 为中文**

完整内容：

```markdown
# Paper Radar Bot

自动抓取 arXiv 最新论文，调用 OpenAI 兼容模型生成中文总结，输出带日期的 HTML 报告。支持通过 `topics.yaml` 配置多个领域关键词，每次运行生成一份按领域分节的单文件报告。

## 快速开始（Windows）

1. 安装 Python 3.11+
2. `pip install -r requirements.txt`
3. 复制 `.env.example` 为 `.env`，填写 `OPENAI_API_KEY`
4. 双击 `run_paper_radar.bat`

报告保存至 `reports/YYYY-MM-DD.html`，用浏览器直接打开即可。

## 快速开始（Linux / macOS / GitHub Actions）

```bash
pip install -r requirements.txt
cp .env.example .env  # 填写 OPENAI_API_KEY
PYTHONPATH=src python -m paper_radar_bot.main
```

## 领域配置（topics.yaml）

编辑项目根目录的 `topics.yaml` 即可自定义抓取领域和关键词：

```yaml
topics:
  - name: LLM Translation
    keywords:
      - LLM translation
      - large language model translation
    max_results: 10
```

多个关键词在查询时自动以 OR 合并。`topics.yaml` 不存在时程序使用内置默认领域正常运行。

## 配置项说明（.env）

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `OPENAI_API_KEY` | 是 | — | API 密钥 |
| `OPENAI_BASE_URL` | 否 | `https://api.openai.com/v1` | API 基础 URL |
| `OPENAI_MODEL` | 否 | `gpt-4o-mini` | 模型名称 |
| `OUTPUT_FORMAT` | 否 | `html` | 输出格式：`html` 或 `markdown` |
| `ARXIV_QUERY` | 否 | `cat:cs.AI` | 仅在 topics.yaml 不存在时作为回退查询 |
| `ARXIV_MAX_RESULTS` | 否 | `10` | 回退模式下的最大结果数 |
| `REPORT_TIMEZONE` | 否 | `Asia/Shanghai` | 时区标签（信息性） |
| `REPORT_LOCALE` | 否 | `zh_CN` | 地区标签（信息性） |

## 运行测试

```bash
PYTHONPATH=src pytest tests/ -v
```
```

- [ ] **Step 4: 提交**

```bash
git add topics.yaml README.md
git commit -m "docs: add topics.yaml with default topics; rewrite README in Chinese"
```

- [ ] **Step 5: 推送**

```bash
git push
```

---

## 规格覆盖自审

| 规格需求 | 对应任务 |
|----------|----------|
| README 改写为中文 | Task 7 |
| 设计文档改写为中文 | 已在 brainstorming 阶段完成（`docs/superpowers/specs/2026-06-21-v2-design.md`） |
| topics.yaml 支持多领域多关键词 | Task 1（数据类）+ Task 7（文件） |
| 关键词 OR 合并查询 | Task 1（`Topic.arxiv_query` 属性） |
| 默认三个领域 | Task 1（`_DEFAULT_TOPICS`）+ Task 7（`topics.yaml`） |
| topics.yaml 不存在时回退 ARXIV_QUERY | Task 1（`load_topics` 逻辑） |
| HTML 默认输出 | Task 2（`output_format` 默认 `"html"`）+ Task 3（渲染器） |
| Markdown 可选 | Task 2 + Task 5（`writer.py`） |
| 按领域分节展示 | Task 3（HTML）+ Task 4（Markdown） |
| 顶部领域导航（HTML） | Task 3（`<nav>` 锚点） |
| 单文件离线 HTML | Task 3（内嵌 CSS，无外部依赖） |
| 全量单元测试通过 | Task 6 Step 4（36 个测试） |
