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
    """Scrape HF weekly trending page; return up to top_n arXiv IDs in ranking order."""
    return _fetch_ids_from_url(_HF_TRENDING_URL, top_n, label="weekly")
