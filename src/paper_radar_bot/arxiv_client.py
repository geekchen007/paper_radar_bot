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
