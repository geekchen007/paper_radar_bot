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
