# HuggingFace 热门论文模块设计文档

## 目标

在现有 Paper Radar Bot 基础上，新增一个独立模块：每日抓取 HuggingFace 热门论文的 Daily Top 10 与 Weekly Top 10，通过 arXiv API 获取完整摘要，调用 LLM 翻译为中文，输出一份独立的 HTML 报告。

## 范围

### 第一版包含

- 抓取 `https://huggingface.co/papers`（每日热门）提取 arXiv ID，取前 10
- 抓取 `https://huggingface.co/papers/trending`（每周热门）提取 arXiv ID，取前 10
- 通过 arXiv API `id_list=` 批量拉取论文元数据（标题、作者、发布时间、摘要）
- 默认仅翻译摘要（轻量 LLM 调用），可通过 `HF_SUMMARIZE_MODE=full` 切换为结构化总结
- 生成独立 HTML 报告，文件名格式 `reports/prbHF热门论文_YYYYMMDD.html`
- 独立入口 `hf_main.py`，可单独运行，不影响现有 arXiv 日报流程

### 第一版不包含

- HuggingFace 官方 SDK / Hub API 集成（使用 HTML 抓取）
- upvote 数展示（HF 页面动态渲染，不在静态 HTML 中）
- 历史归档 / 按日期回溯
- Markdown 输出格式（仅 HTML）

## 用户体验

运行方式与现有 arXiv 日报相同：

```bash
PYTHONPATH=src python -m paper_radar_bot.hf_main
```

生成报告 `reports/prbHF热门论文_20260622.html`，包含两个可折叠区块：

- **HuggingFace 每日 Top 10**：今日热门论文，英文标题 + 中文摘要
- **HuggingFace 每周 Top 10**：本周热门论文，英文标题 + 中文摘要

报告样式复用现有 `html_renderer.py`，左侧目录、可折叠卡片风格不变。

## 架构

### 新增文件

| 文件 | 职责 |
|------|------|
| `src/paper_radar_bot/hf_client.py` | 抓取 HF 热门页 HTML，用正则提取 arXiv ID，去重，返回有序列表 |
| `src/paper_radar_bot/hf_main.py` | 独立编排入口：抓取 → 拉摘要 → 翻译 → 渲染 → 写文件 |
| `tests/test_hf_client.py` | 用静态 HTML fixture 测试 ID 提取逻辑（无网络请求） |

### 修改文件

| 文件 | 变更 |
|------|------|
| `src/paper_radar_bot/arxiv_client.py` | 新增 `fetch_papers_by_ids(arxiv_ids: list[str]) -> list[Paper]`，按 ID 列表顺序返回 |
| `src/paper_radar_bot/summarizer.py` | 新增 `translate_abstract(paper: Paper, config: Config) -> Summary`，仅翻译摘要 |
| `src/paper_radar_bot/html_renderer.py` | `render_report()` 增加可选 `title: str = "Paper Radar 日报"` 参数，向后兼容 |
| `src/paper_radar_bot/config.py` | `Config` 新增 `hf_summarize_mode: str`，`load_config()` 读取 `HF_SUMMARIZE_MODE` |
| `.env.example` | 新增 `HF_SUMMARIZE_MODE=translate` 文档注释 |

## 数据流

```
1. hf_client.fetch_daily_ids(top_n=10)
   GET https://huggingface.co/papers
   正则提取 /papers/{arxiv_id} 链接，去重，取前 10

   hf_client.fetch_weekly_ids(top_n=10)
   GET https://huggingface.co/papers/trending
   正则提取 /papers/{arxiv_id} 链接，去重，取前 10

2. arxiv_client.fetch_papers_by_ids(ids)
   GET https://export.arxiv.org/api/query?id_list=2406.xxx,2406.yyy,...
   复用现有 _parse_atom()，按输入 ID 顺序排列结果

3. 按 config.hf_summarize_mode 分发：
   "translate" → summarizer.translate_abstract(paper, config)
     LLM prompt：仅翻译摘要为中文，无 JSON 格式要求
     返回 Summary(chinese_abstract=..., highlights=[], applications=[])
   "full"       → summarizer.summarize(paper, config, date_str)
     复用现有结构化总结流程

4. 构建 TopicResult 列表：
   [TopicResult(Topic("HuggingFace 每日 Top 10"), daily_papers, daily_summaries),
    TopicResult(Topic("HuggingFace 每周 Top 10"), weekly_papers, weekly_summaries)]

5. html_renderer.render_report(results, date_str, title="HuggingFace 热门论文")
   复用现有渲染器，title 参数决定页面 <h1> 和 <title>

6. writer.write_report(content, date_str, output_format="html", report_title="HF热门论文")
   → reports/prbHF热门论文_YYYYMMDD.html
```

## 关键接口

```python
# hf_client.py
def fetch_daily_ids(top_n: int = 10) -> list[str]:
    """Scrape HF daily papers page; return up to top_n arXiv IDs in ranking order."""

def fetch_weekly_ids(top_n: int = 10) -> list[str]:
    """Scrape HF trending page; return up to top_n arXiv IDs in ranking order."""

def _extract_arxiv_ids(html: str, top_n: int) -> list[str]:
    """Extract arXiv IDs from HF papers page HTML; dedup, preserve order."""

# arxiv_client.py（新增）
def fetch_papers_by_ids(arxiv_ids: list[str]) -> list[Paper]:
    """Fetch specific papers via arXiv id_list param; results ordered to match input."""

# summarizer.py（新增）
def translate_abstract(paper: Paper, config: Config) -> Summary:
    """Translate paper abstract to Chinese; return Summary with only chinese_abstract set."""

# html_renderer.py（签名修改，向后兼容）
def render_report(
    results: list[TopicResult],
    date_str: str,
    title: str = "Paper Radar 日报",
) -> str: ...
```

## 配置

新增环境变量（均为可选，带默认值）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `HF_SUMMARIZE_MODE` | `translate` | `translate`：仅翻译摘要；`full`：结构化总结 |

现有变量（`OPENAI_API_KEY`、`OPENAI_MODEL` 等）直接复用，无需额外配置。

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| HF 页面请求失败（HTTP 错误、超时） | 退出并打印错误；daily / weekly 独立处理，互不影响 |
| 解析结果为 0 个 ID | 打印警告，跳过该区块，报告中对应区块显示"暂无数据" |
| arXiv 批量查询失败 | 退出并打印错误 |
| arXiv 返回条数少于请求条数 | 正常处理，报告如实显示实际数量 |
| 单篇 LLM 翻译失败 | `Summary.error` 标记，卡片显示"翻译失败"，其余论文继续 |
| `HF_SUMMARIZE_MODE` 值非法 | `load_config()` 退出并给出明确提示 |

## 测试策略

- `tests/test_hf_client.py`：提供两段静态 HTML fixture，测试 `_extract_arxiv_ids()` 的正确提取、去重、数量截断行为，无任何 HTTP 请求
- `arxiv_client.py`：`fetch_papers_by_ids()` 底层复用 `_parse_atom()`，已有 8 个单元测试自动覆盖解析逻辑，无需新增测试
- `html_renderer.py`：`title` 参数仅影响字符串插值，现有测试继续通过，无需新增
- 翻译与端到端流程：LLM 调用手动验证或通过 GitHub Actions 验证

## 文件命名

```
reports/prbHF热门论文_20260622.html
```

与现有命名规则 `prb{report_title}_{YYYYMMDD}.html` 完全一致，无需修改 `writer.py`。

## 验收标准

- `PYTHONPATH=src python -m paper_radar_bot.hf_main` 可正常运行
- 生成报告包含"每日 Top 10"和"每周 Top 10"两个区块
- 每个区块最多 10 篇论文，每篇包含英文标题、作者、发布时间、arXiv 链接、中文摘要
- 单篇翻译失败不中断整体运行
- `PYTHONPATH=src pytest tests/ -v` 全部通过（包含新增 test_hf_client.py）
- 现有 arXiv 日报功能不受影响
