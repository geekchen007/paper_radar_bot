"""Unit tests for arXiv Atom XML parsing (no HTTP calls)."""

import textwrap

from paper_radar_bot.arxiv_client import _parse_atom


SAMPLE_ATOM = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>Attention Is All You Need</title>
        <author><name>Ashish Vaswani</name></author>
        <author><name>Noam Shazeer</name></author>
        <published>2017-06-12T17:57:34Z</published>
        <id>http://arxiv.org/abs/1706.03762v5</id>
        <summary>The dominant sequence transduction models...</summary>
        <link href="http://arxiv.org/abs/1706.03762v5" rel="alternate" type="text/html"/>
      </entry>
    </feed>
""")


def test_parse_atom_returns_papers():
    papers = _parse_atom(SAMPLE_ATOM)
    assert len(papers) == 1


def test_parse_atom_title():
    papers = _parse_atom(SAMPLE_ATOM)
    assert papers[0].title == "Attention Is All You Need"


def test_parse_atom_authors():
    papers = _parse_atom(SAMPLE_ATOM)
    assert papers[0].authors == ["Ashish Vaswani", "Noam Shazeer"]


def test_parse_atom_published():
    papers = _parse_atom(SAMPLE_ATOM)
    assert papers[0].published == "2017-06-12T17:57:34Z"


def test_parse_atom_arxiv_id():
    papers = _parse_atom(SAMPLE_ATOM)
    assert papers[0].arxiv_id == "1706.03762"


def test_parse_atom_url():
    papers = _parse_atom(SAMPLE_ATOM)
    assert papers[0].url == "https://arxiv.org/abs/1706.03762"


def test_parse_atom_abstract():
    papers = _parse_atom(SAMPLE_ATOM)
    assert "dominant sequence transduction" in papers[0].abstract


def test_parse_atom_empty_feed():
    empty = '<feed xmlns="http://www.w3.org/2005/Atom"></feed>'
    assert _parse_atom(empty) == []
