# HuggingFace 热门论文模块 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增一个独立模块，抓取 HuggingFace 每日 / 每周热门论文 Top 10，通过 arXiv API 获取摘要，LLM 翻译为中文，输出独立 HTML 报告。

**Architecture:** `hf_client.py` 抓取 HF 热门页 HTML 并提取 arXiv ID；`arxiv_client.py` 扩展 `fetch_papers_by_ids()` 按 ID 批量拉取元数据；`summarizer.py` 扩展 `translate_abstract()` 仅翻译摘要；`hf_main.py` 编排全流程，将结果构建为两个 `TopicResult` 对象后复用现有 `html_renderer.render_report()`。

**Tech Stack:** Python 3.11+, `requests`, `openai` SDK, `pytest`；HTML 解析用标准库 `re`；无新增第三方依赖。

## Global Constraints

- Python ≥ 3.11；源码在 `src/paper_radar_bot/`，测试在 `tests/`
- 公开函数/方法必须有类型注解和 docstring
- 行长 ≤ 120 字符；`snake_case` 函数/变量，`PascalCase` 类，`UPPER_SNAKE_CASE` 常量
- 禁止裸 `except:`；异常至少 logging 记录
- f-string 优先；`is`/`is not` 比较 None
- `PYTHONPATH=src` 运行所有命令
- Commit 格式：`<type>(<scope>): <subject>`

---

## File Map

| 文件 | 角色 |
|------|------|
| `src/paper_radar_bot/config.py` | 新增 `hf_summarize_mode` 字段和 `HF_SUMMARIZE_MODE` 读取 |
| `src/paper_radar_bot/html_renderer.py` | `render_report()` 增加可选 `title` 参数 |
| `src/paper_radar_bot/arxiv_client.py` | 新增 `fetch_papers_by_ids()` |
| `src/paper_radar_bot/hf_client.py` | 新建：抓取 HF 热门页，提取 arXiv ID 列表 |
| `src/paper_radar_bot/summarizer.py` | 新增 `translate_abstract()`（仅翻译，无结构化 JSON）|
| `src/paper_radar_bot/hf_main.py` | 新建：HF 热门报告独立入口 |
| `tests/test_hf_client.py` | 新建：`_extract_arxiv_ids()` 单元测试（静态 HTML fixture）|
| `.env.example` | 补充 `HF_SUMMARIZE_MODE` 说明 |

---

### Task 1: Config 扩展 + `.env.example`

**Files:**
- Modify: `src/paper_radar_bot/config.py`
- Modify: `.env.example`

**Interfaces:**
- Produces: `Config.hf_summarize_mode: str`（值为 `"translate"` 或 `"full"`）

- [ ] **Step 1: 修改 `Config` dataclass，新增字段**

在 `src/paper_radar_bot/config.py` 的 `Config` dataclass 末尾新增一行：

```python
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
    hf_summarize_mode: str  # "translate" or "full"
```

- [ ] **Step 2: 在 `load_config()` 中读取新环境变量**

在 `load_config()` 函数内，`raw_format` 校验块之后、`return Config(...)` 之前，插入：

```python
    raw_hf_mode = os.getenv("HF_SUMMARIZE_MODE", "translate").lower()
    if raw_hf_mode not in ("translate", "full"):
        print(f"ERROR: HF_SUMMARIZE_MODE must be 'translate' or 'full', got: {raw_hf_mode!r}", file=sys.stderr)
        sys.exit(1)
```

- [ ] **Step 3: 在 `return Config(...)` 中补充新字段**

将 `return Config(...)` 改为：

```python
    return Config(
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL", _DEFAULTS["OPENAI_BASE_URL"]),
        model=os.getenv("OPENAI_MODEL", _DEFAULTS["OPENAI_MODEL"]),
        arxiv_query=os.getenv("ARXIV_QUERY", _DEFAULTS["ARXIV_QUERY"]),
        arxiv_max_results=max_results,
        timezone=os.getenv("REPORT_TIMEZONE", _DEFAULTS["REPORT_TIMEZONE"]),
        locale=os.getenv("REPORT_LOCALE", _DEFAULTS["REPORT_LOCALE"]),
        output_format=raw_format,
        hf_summarize_mode=raw_hf_mode,
    )
```

- [ ] **Step 4: 更新 `.env.example`**

在文件末尾追加：

```dotenv
# HuggingFace 热门论文模块（可选）
# translate：仅翻译摘要（默认）；full：结构化总结（复用 arXiv 日报流程）
HF_SUMMARIZE_MODE=translate
```

- [ ] **Step 5: 验证 import 和默认值**

```bash
PYTHONPATH=src python -c "
from paper_radar_bot.config import load_config
import os; os.environ['OPENAI_API_KEY'] = 'test'
c = load_config()
print(c.hf_summarize_mode)
"
```

预期输出：`translate`

- [ ] **Step 6: Commit**

```bash
git add src/paper_radar_bot/config.py .env.example
git commit -m "feat(config): add HF_SUMMARIZE_MODE config field"
```

---

### Task 2: `html_renderer.py` 增加可选 `title` 参数

**Files:**
- Modify: `src/paper_radar_bot/html_renderer.py`

**Interfaces:**
- Consumes: 无新依赖
- Produces: `render_report(results, date_str, title="Paper Radar 日报") -> str`（向后兼容）

- [ ] **Step 1: 确认现有测试通过**

```bash
PYTHONPATH=src pytest tests/test_html_renderer.py -v
```

预期：全部 PASS（作为后续对比基准）。

- [ ] **Step 2: 修改 `render_report` 函数签名**

将 `html_renderer.py` 中第 331 行附近的函数定义改为：

```python
def render_report(results: list[TopicResult], date_str: str, title: str = "Paper Radar 日报") -> str:
    """Render all topic results into a complete single-file HTML report."""
```

- [ ] **Step 3: 替换函数体内的硬编码标题**

在同一函数体内，找到以下两处硬编码字符串并替换：

```python
# 修改前：
f'<title>Paper Radar 日报 — {_e(date_str)}</title>\n'
# 修改后：
f'<title>{_e(title)} — {_e(date_str)}</title>\n'

# 修改前：
f'<h1>Paper Radar 日报 — {_e(date_str)}</h1>\n'
# 修改后：
f'<h1>{_e(title)} — {_e(date_str)}</h1>\n'
```

- [ ] **Step 4: 确认现有测试全部仍然通过**

```bash
PYTHONPATH=src pytest tests/test_html_renderer.py -v
```

预期：全部 PASS（默认参数保持向后兼容）。

- [ ] **Step 5: 确认新 title 参数生效**

```bash
PYTHONPATH=src python -c "
from paper_radar_bot.html_renderer import render_report
from paper_radar_bot.models import Paper, Summary, Topic, TopicResult
p = Paper('T','['A']','2026-01-01','0001.00001','abs','https://arxiv.org/abs/0001.00001')
s = Summary(chinese_abstract='中文')
r = TopicResult(topic=Topic('每日',['kw']),papers=[p],summaries=[s])
html = render_report([r], '2026-06-22', title='HuggingFace 热门论文')
assert 'HuggingFace 热门论文' in html
print('ok')
"
```

预期输出：`ok`

- [ ] **Step 6: Commit**

```bash
git add src/paper_radar_bot/html_renderer.py
git commit -m "feat(html_renderer): add optional title param to render_report"
```

---

### Task 3: `arxiv_client.py` 新增 `fetch_papers_by_ids()`

**Files:**
- Modify: `src/paper_radar_bot/arxiv_client.py`

**Interfaces:**
- Consumes: 现有 `_parse_atom()`, `_ARXIV_API`, `_HEADERS`
- Produces: `fetch_papers_by_ids(arxiv_ids: list[str]) -> list[Paper]`
  - 返回顺序与输入 `arxiv_ids` 一致
  - arXiv 未返回的 ID 直接跳过（不报错）

- [ ] **Step 1: 在 `arxiv_client.py` 末尾追加新函数**

```python
def fetch_papers_by_ids(arxiv_ids: list[str]) -> list[Paper]:
    """Fetch specific papers from arXiv by ID list; results ordered to match input."""
    if not arxiv_ids:
        return []

    params = {
        "id_list": ",".join(arxiv_ids),
        "max_results": len(arxiv_ids),
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

    papers = _parse_atom(response.text)
    papers_by_id = {p.arxiv_id: p for p in papers}
    return [papers_by_id[aid] for aid in arxiv_ids if aid in papers_by_id]
```

- [ ] **Step 2: 验证空列表边界情况**

```bash
PYTHONPATH=src python -c "
from paper_radar_bot.arxiv_client import fetch_papers_by_ids
result = fetch_papers_by_ids([])
assert result == [], f'Expected [], got {result}'
print('ok')
"
```

预期输出：`ok`

- [ ] **Step 3: 验证 import 包含新函数**

```bash
PYTHONPATH=src python -c "from paper_radar_bot.arxiv_client import fetch_papers_by_ids; print('ok')"
```

预期输出：`ok`

- [ ] **Step 4: 运行 arXiv 相关测试，确认现有功能不受影响**

```bash
PYTHONPATH=src pytest tests/test_arxiv_client.py -v
```

预期：全部 PASS。

- [ ] **Step 5: Commit**

```bash
git add src/paper_radar_bot/arxiv_client.py
git commit -m "feat(arxiv_client): add fetch_papers_by_ids for batch ID lookup"
```

---

### Task 4: `hf_client.py` + 单元测试

**Files:**
- Create: `src/paper_radar_bot/hf_client.py`
- Create: `tests/test_hf_client.py`

**Interfaces:**
- Produces:
  - `fetch_daily_ids(top_n: int = 10) -> list[str]`：抓取 `https://huggingface.co/papers`，返回 arXiv ID 列表
  - `fetch_weekly_ids(top_n: int = 10) -> list[str]`：抓取 `https://huggingface.co/papers/trending`，返回 arXiv ID 列表
  - `_extract_arxiv_ids(html: str, top_n: int) -> list[str]`：从 HTML 文本提取有序去重 ID 列表（可测试）

- [ ] **Step 1: 写失败测试**

创建 `tests/test_hf_client.py`：

```python
"""Unit tests for HuggingFace papers page scraping (no HTTP calls)."""

from paper_radar_bot.hf_client import _extract_arxiv_ids

_DAILY_HTML = """
<!DOCTYPE html>
<html>
<body>
<article>
  <a href="/papers/2506.00001">Paper Alpha</a>
  <a href="/papers/2506.00001">duplicate link</a>
</article>
<article>
  <a href="/papers/2506.00002">Paper Beta</a>
</article>
<article>
  <a href="/papers/2506.00003v2">Paper Gamma with version</a>
</article>
<article>
  <a href="/papers/2506.00004">Paper Delta</a>
</article>
<article>
  <a href="/papers/2506.00005">Paper Epsilon</a>
</article>
<a href="/datasets/something">Not a paper</a>
<a href="/papers/not-an-id">Malformed</a>
</body>
</html>
"""

_EMPTY_HTML = "<html><body><p>No papers today.</p></body></html>"


def test_extract_returns_list():
    ids = _extract_arxiv_ids(_DAILY_HTML, top_n=10)
    assert isinstance(ids, list)


def test_extract_correct_ids():
    ids = _extract_arxiv_ids(_DAILY_HTML, top_n=10)
    assert "2506.00001" in ids
    assert "2506.00002" in ids


def test_extract_strips_version_suffix():
    ids = _extract_arxiv_ids(_DAILY_HTML, top_n=10)
    assert "2506.00003" in ids
    assert "2506.00003v2" not in ids


def test_extract_deduplicates():
    ids = _extract_arxiv_ids(_DAILY_HTML, top_n=10)
    assert ids.count("2506.00001") == 1


def test_extract_preserves_order():
    ids = _extract_arxiv_ids(_DAILY_HTML, top_n=10)
    assert ids.index("2506.00001") < ids.index("2506.00002")
    assert ids.index("2506.00002") < ids.index("2506.00003")


def test_extract_ignores_non_paper_links():
    ids = _extract_arxiv_ids(_DAILY_HTML, top_n=10)
    assert all(id_.replace(".", "").replace("v", "").isdigit() or "." in id_ for id_ in ids)
    for id_ in ids:
        assert id_[4] == "."


def test_extract_top_n_truncation():
    ids = _extract_arxiv_ids(_DAILY_HTML, top_n=2)
    assert len(ids) == 2
    assert ids[0] == "2506.00001"
    assert ids[1] == "2506.00002"


def test_extract_empty_page():
    ids = _extract_arxiv_ids(_EMPTY_HTML, top_n=10)
    assert ids == []
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
PYTHONPATH=src pytest tests/test_hf_client.py -v
```

预期：`ImportError` 或 `ModuleNotFoundError`（`hf_client` 尚未创建）。

- [ ] **Step 3: 创建 `src/paper_radar_bot/hf_client.py`**

```python
"""Scrape HuggingFace papers pages and extract trending arXiv IDs."""

import logging
import re
import sys

import requests

_HF_DAILY_URL = "https://huggingface.co/papers"
_HF_TRENDING_URL = "https://huggingface.co/papers/trending"
_ARXIV_ID_RE = re.compile(r'/papers/(\d{4}\.\d{4,5})')
_HEADERS = {
    "User-Agent": "paper_radar_bot/0.1 (research aggregator)",
    "Accept": "text/html",
}

logger = logging.getLogger(__name__)


def _extract_arxiv_ids(html: str, top_n: int) -> list[str]:
    """Extract arXiv IDs from HF papers page HTML; deduplicate, preserve order, truncate to top_n."""
    seen: set[str] = set()
    result: list[str] = []
    for match in _ARXIV_ID_RE.finditer(html):
        arxiv_id = match.group(1)
        if arxiv_id not in seen:
            seen.add(arxiv_id)
            result.append(arxiv_id)
            if len(result) >= top_n:
                break
    return result


def _fetch_ids_from_url(url: str, top_n: int, label: str) -> list[str]:
    """Fetch a HF papers page and return extracted arXiv IDs."""
    try:
        response = requests.get(url, headers=_HEADERS, timeout=30)
        response.raise_for_status()
    except requests.HTTPError as e:
        print(
            f"ERROR: Failed to fetch HF {label} page (HTTP {e.response.status_code}): {e}",
            file=sys.stderr,
        )
        return []
    except requests.RequestException as e:
        print(f"ERROR: Failed to fetch HF {label} page: {e}", file=sys.stderr)
        return []

    ids = _extract_arxiv_ids(response.text, top_n)
    if not ids:
        logger.warning("No arXiv IDs found on HF %s page (%s).", label, url)
    return ids


def fetch_daily_ids(top_n: int = 10) -> list[str]:
    """Scrape HF daily papers page; return up to top_n arXiv IDs in ranking order."""
    return _fetch_ids_from_url(_HF_DAILY_URL, top_n, label="daily")


def fetch_weekly_ids(top_n: int = 10) -> list[str]:
    """Scrape HF trending page; return up to top_n arXiv IDs in ranking order."""
    return _fetch_ids_from_url(_HF_TRENDING_URL, top_n, label="weekly")
```

- [ ] **Step 4: 运行测试，确认全部通过**

```bash
PYTHONPATH=src pytest tests/test_hf_client.py -v
```

预期：全部 8 个测试 PASS。

- [ ] **Step 5: 运行全量测试，确认现有功能不受影响**

```bash
PYTHONPATH=src pytest tests/ -v
```

预期：全部 PASS。

- [ ] **Step 6: Commit**

```bash
git add src/paper_radar_bot/hf_client.py tests/test_hf_client.py
git commit -m "feat(hf_client): add HuggingFace trending papers scraper with unit tests"
```

---

### Task 5: `summarizer.py` 新增 `translate_abstract()`

**Files:**
- Modify: `src/paper_radar_bot/summarizer.py`

**Interfaces:**
- Consumes: `Paper`（from `models.py`），`Config`（from Task 1，含 `api_key`, `base_url`, `model`）
- Produces: `translate_abstract(paper: Paper, config: Config) -> Summary`
  - 成功：`Summary(chinese_abstract="…中文…", highlights=[], applications=[], error=None)`
  - 失败：`Summary(chinese_abstract="", highlights=[], applications=[], error="…")`

- [ ] **Step 1: 在 `summarizer.py` 末尾追加新函数**

```python
_TRANSLATE_SYSTEM = (
    "你是专业的学术论文翻译助手。"
    "将英文摘要翻译为流畅准确的中文，保持学术用语，不添加额外解释或内容。"
)


def translate_abstract(paper: Paper, config: Config) -> Summary:
    """Translate paper abstract to Chinese; return Summary with only chinese_abstract set."""
    client = OpenAI(api_key=config.api_key, base_url=config.base_url)
    user_message = f"请将以下英文论文摘要翻译为中文：\n\n{paper.abstract}"

    try:
        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": _TRANSLATE_SYSTEM},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
        )
        chinese_abstract = (response.choices[0].message.content or "").strip()
        return Summary(chinese_abstract=chinese_abstract, highlights=[], applications=[])
    except (OpenAIError, IndexError) as e:
        logger.warning("Translation failed for paper %r: %s", paper.arxiv_id, e)
        return Summary(chinese_abstract="", highlights=[], applications=[], error=str(e))
```

- [ ] **Step 2: 验证 import**

```bash
PYTHONPATH=src python -c "from paper_radar_bot.summarizer import translate_abstract; print('ok')"
```

预期输出：`ok`

- [ ] **Step 3: Commit**

```bash
git add src/paper_radar_bot/summarizer.py
git commit -m "feat(summarizer): add translate_abstract for lightweight abstract translation"
```

---

### Task 6: `hf_main.py` 编排入口

**Files:**
- Create: `src/paper_radar_bot/hf_main.py`

**Interfaces:**
- Consumes:
  - `hf_client.fetch_daily_ids()`, `hf_client.fetch_weekly_ids()`（Task 4）
  - `arxiv_client.fetch_papers_by_ids(ids: list[str]) -> list[Paper]`（Task 3）
  - `config.load_config() -> Config`（Task 1，含 `hf_summarize_mode`）
  - `summarizer.translate_abstract(paper, config) -> Summary`（Task 5）
  - `summarizer.summarize(paper, config, date_str) -> Summary`（现有）
  - `models.Topic`, `models.TopicResult`
  - `html_renderer.render_report(results, date_str, title) -> str`（Task 2）
  - `writer.write_report(content, date_str, output_format, report_title) -> str`（现有）
- Produces: `reports/prbHF热门论文_YYYYMMDD.html`

- [ ] **Step 1: 创建 `src/paper_radar_bot/hf_main.py`**

```python
"""Entry point for the HuggingFace trending papers report."""

import logging
from datetime import datetime, timezone

from paper_radar_bot.arxiv_client import fetch_papers_by_ids
from paper_radar_bot.config import Config, load_config
from paper_radar_bot.hf_client import fetch_daily_ids, fetch_weekly_ids
from paper_radar_bot.html_renderer import render_report
from paper_radar_bot.models import Summary, Topic, TopicResult
from paper_radar_bot.summarizer import summarize, translate_abstract
from paper_radar_bot.writer import write_report

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

_HF_REPORT_TITLE = "HF热门论文"
_REPORT_DISPLAY_TITLE = "HuggingFace 热门论文"


def _process_section(
    label: str,
    arxiv_ids: list[str],
    config: Config,
    date_str: str,
) -> TopicResult:
    """Fetch papers and generate summaries for one section (daily or weekly)."""
    topic = Topic(name=label, keywords=[], max_results=len(arxiv_ids))

    if not arxiv_ids:
        logger.warning("No IDs for section %r, section will be empty.", label)
        return TopicResult(topic=topic, papers=[], summaries=[])

    logger.info("  Fetching %d papers from arXiv...", len(arxiv_ids))
    papers = fetch_papers_by_ids(arxiv_ids)
    logger.info("  Retrieved %d papers.", len(papers))

    summaries: list[Summary] = []
    for i, paper in enumerate(papers, start=1):
        logger.info("  [%d/%d] Processing: %s", i, len(papers), paper.title[:60])
        if config.hf_summarize_mode == "full":
            summary = summarize(paper, config, date_str)
        else:
            summary = translate_abstract(paper, config)
        if summary.error is not None:
            logger.warning("    Failed: %s", summary.error)
        summaries.append(summary)

    return TopicResult(topic=topic, papers=papers, summaries=summaries)


def main() -> None:
    """Fetch HF trending papers, translate, render, and write the report."""
    config = load_config()
    date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    logger.info(
        "HF trending report for %s (mode: %s)",
        date_str,
        config.hf_summarize_mode,
    )

    logger.info("Fetching HuggingFace daily top 10...")
    daily_ids = fetch_daily_ids(top_n=10)
    logger.info("Found %d daily IDs.", len(daily_ids))

    logger.info("Fetching HuggingFace weekly trending top 10...")
    weekly_ids = fetch_weekly_ids(top_n=10)
    logger.info("Found %d weekly IDs.", len(weekly_ids))

    daily_result = _process_section("HuggingFace 每日 Top 10", daily_ids, config, date_str)
    weekly_result = _process_section("HuggingFace 每周 Top 10", weekly_ids, config, date_str)

    results = [daily_result, weekly_result]
    report = render_report(results, date_str, title=_REPORT_DISPLAY_TITLE)
    path = write_report(
        report,
        date_str,
        output_format="html",
        report_title=_HF_REPORT_TITLE,
    )
    logger.info("Report written to: %s", path)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 验证完整 import 链**

```bash
PYTHONPATH=src python -c "from paper_radar_bot.hf_main import main; print('ok')"
```

预期输出：`ok`

- [ ] **Step 3: 运行全量测试，确认无回归**

```bash
PYTHONPATH=src pytest tests/ -v
```

预期：全部 PASS（含新增的 `test_hf_client.py`）。

- [ ] **Step 4: Commit**

```bash
git add src/paper_radar_bot/hf_main.py
git commit -m "feat(hf_main): add HuggingFace trending papers report entry point"
```

---

## Acceptance Checklist

- [ ] `PYTHONPATH=src pytest tests/ -v` 全部通过，包含 `test_hf_client.py`
- [ ] `PYTHONPATH=src python -m paper_radar_bot.hf_main` 可正常运行（需 `.env` 配置 API Key）
- [ ] 生成报告包含"HuggingFace 每日 Top 10"和"HuggingFace 每周 Top 10"两个区块
- [ ] 每篇论文卡片含英文标题、中文摘要、arXiv 链接
- [ ] 单篇翻译失败不中断整体运行，卡片显示"总结失败"
- [ ] 现有 `python -m paper_radar_bot.main` arXiv 日报功能不受影响
- [ ] 新报告文件名格式：`reports/prbHF热门论文_YYYYMMDD.html`
