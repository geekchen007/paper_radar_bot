# Paper Radar Bot Design

## Goal

Build a small standalone Python project that fetches recent arXiv papers for configured topics, generates Chinese summaries with an OpenAI-compatible model, writes a dated Markdown report, and can be run either locally through a `.bat` file or automatically through GitHub Actions.

## Scope

This first version is intentionally narrow:

- Fetch papers from the arXiv API only
- Filter papers by configured search keywords
- Generate Chinese summaries for each paper
- Render one Markdown report per run into `reports/`
- Provide a Windows `.bat` entrypoint for one-click local execution
- Provide a GitHub Actions workflow for scheduled runs and auto-commit

Out of scope for this version:

- Multi-source aggregation beyond arXiv
- Deduplication across remote databases
- Web UI or dashboard
- Database storage
- Semantic ranking or citation graph analysis

## User Experience

The project supports two primary ways to run:

1. Local Windows execution through `run_paper_radar.bat`
2. Scheduled GitHub execution through Actions once the repository is pushed

Each run produces a Markdown report named by date, for example `reports/2026-06-21.md`. The report contains:

- Run metadata
- Search topics used
- Paper title
- Authors
- Published date
- arXiv link
- Chinese summary
- Key highlights
- Potential applications

## Architecture

The codebase will be split into small modules with clear responsibilities:

- `config.py`: loads environment variables and validates runtime configuration
- `models.py`: dataclasses for normalized paper records and summary output
- `arxiv_client.py`: requests and parses arXiv Atom responses
- `summarizer.py`: calls the OpenAI-compatible chat completion API
- `renderer.py`: converts normalized paper data into Markdown
- `writer.py`: creates output directories and saves reports
- `main.py`: orchestration entrypoint

This keeps fetch, summarize, render, and write concerns separated so future changes can replace one piece without rewriting the rest.

## Data Flow

1. Load config from environment variables and optional `.env`
2. Query arXiv using configured keywords and max result count
3. Normalize API responses into internal paper records
4. For each paper, generate a structured Chinese summary
5. Render all paper records into one dated Markdown report
6. Save the report under `reports/`

## Configuration

The first version will use environment variables with a documented `.env.example`.

Required:

- `OPENAI_API_KEY`

Optional with defaults:

- `OPENAI_BASE_URL`
- `OPENAI_MODEL`
- `ARXIV_QUERY`
- `ARXIV_MAX_RESULTS`
- `REPORT_TIMEZONE`
- `REPORT_LOCALE`

The default query will target AI-related frontier topics so the project works out of the box after adding an API key.

## Error Handling

The CLI should fail clearly and early when configuration is missing or invalid.

- Missing API key: exit with a readable message
- arXiv request failure: exit with status code and concise error detail
- summary generation failure for one paper: keep the paper and mark the summary section as failed instead of aborting the entire run
- file write failure: exit with a readable filesystem error

## Testing Strategy

This project will start with focused unit tests for stable logic:

- arXiv response parsing into normalized records
- Markdown rendering from normalized records
- output path generation and file writing

External HTTP calls will not be exercised in unit tests. Those integration paths will remain manual- or workflow-verified in this first version.

## Repository Layout

Planned structure:

```text
paper_radar_bot/
  .github/workflows/
  docs/superpowers/specs/
  reports/
  src/paper_radar_bot/
  tests/
  .env.example
  README.md
  requirements.txt
  run_paper_radar.bat
```

## Tradeoffs

### Option A: Pure local script only

Pros:

- simplest setup
- no GitHub workflow maintenance

Cons:

- no automatic updating
- no built-in publishing path

### Option B: Python CLI plus `.bat` plus GitHub Actions

Pros:

- strong local usability on Windows
- easy scheduled automation
- same Python entrypoint serves both local and cloud execution

Cons:

- slightly more setup surface

Recommended: Option B, because it gives local one-click execution without giving up unattended GitHub updates.

### Option C: Full web app

Pros:

- richer browsing experience

Cons:

- much larger scope
- unnecessary for the first milestone

## Acceptance Criteria

The first version is successful when:

- a user can fill `.env`
- a user can run `run_paper_radar.bat`
- the script generates a dated Markdown report under `reports/`
- the report includes fetched paper metadata and Chinese summaries
- the repository includes a GitHub Actions workflow for scheduled execution and auto-commit
- unit tests for parse, render, and write logic pass locally
