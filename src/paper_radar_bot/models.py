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
