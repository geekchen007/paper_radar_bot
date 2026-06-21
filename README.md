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
