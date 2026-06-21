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
