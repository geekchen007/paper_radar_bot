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


@dataclass
class Topic:
    """单个领域的配置。"""

    name: str
    keywords: list[str]
    max_results: int = 10
    _override_query: str | None = field(default=None, repr=False, compare=False)

    @property
    def arxiv_query(self) -> str:
        """将关键词列表 OR 拼接为 arXiv 查询串；若设置了 _override_query 则直接返回。"""
        if self._override_query is not None:
            return self._override_query
        return " OR ".join(f'all:"{kw}"' for kw in self.keywords)


@dataclass
class TopicResult:
    """单个领域的抓取与总结结果。"""

    topic: Topic
    papers: list[Paper]
    summaries: list[Summary]
