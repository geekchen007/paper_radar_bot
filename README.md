# Paper Radar Bot

自动抓取 arXiv 最新论文，调用 OpenAI 兼容模型生成中文总结，输出带日期的 HTML 报告。支持通过 `topics.yaml` 配置多个领域关键词，每次运行生成一份按领域分节的单文件报告。

另提供 **HuggingFace 热门论文模块**，每日抓取 HuggingFace Daily / Weekly Top 10，翻译摘要后生成独立 HTML 报告。

## 快速开始（Windows）

1. 安装 Python 3.11+
2. `pip install -r requirements.txt`
3. 复制 `.env.example` 为 `.env`，填写 `OPENAI_API_KEY`
4. 双击 `run_paper_radar.bat`

报告保存至 `reports/prb<主题名>_YYYYMMDD.html`（主题名在 `topics.yaml` 的 `report_title` 中配置），用浏览器直接打开即可。

## 快速开始（Linux / macOS / GitHub Actions）

```bash
pip install -r requirements.txt
cp .env.example .env  # 填写 OPENAI_API_KEY
PYTHONPATH=src python -m paper_radar_bot.main
```

## HuggingFace 热门论文

抓取 [huggingface.co/papers](https://huggingface.co/papers) 每日热门与 [huggingface.co/papers/trending](https://huggingface.co/papers/trending) 每周热门各 Top 10，通过 arXiv API 获取完整元数据，LLM 翻译摘要后生成独立 HTML 报告。

```bash
PYTHONPATH=src python -m paper_radar_bot.hf_main
```

报告保存至 `reports/prbHF热门论文_YYYYMMDD.html`，包含两个可折叠区块：**每日 Top 10** 和 **每周 Top 10**。

默认仅翻译摘要（速度快、调用次数少）。若需结构化总结（中文标题、核心贡献、关键结果等），在 `.env` 中设置：

```dotenv
HF_SUMMARIZE_MODE=full
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
| `OUTPUT_FORMAT` | 否 | `html` | 输出格式：`html` 或 `markdown`（仅 arXiv 日报） |
| `ARXIV_QUERY` | 否 | `cat:cs.AI` | 仅在 topics.yaml 不存在时作为回退查询 |
| `ARXIV_MAX_RESULTS` | 否 | `10` | 回退模式下的最大结果数 |
| `HF_SUMMARIZE_MODE` | 否 | `translate` | HF 模块：`translate` 仅翻译摘要；`full` 结构化总结 |
| `REPORT_TIMEZONE` | 否 | `Asia/Shanghai` | 时区标签（信息性） |
| `REPORT_LOCALE` | 否 | `zh_CN` | 地区标签（信息性） |

## 运行测试

```bash
PYTHONPATH=src pytest tests/ -v
```
