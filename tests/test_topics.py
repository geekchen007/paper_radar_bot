"""Unit tests for topic loading and query construction."""

import os
import tempfile

from paper_radar_bot.models import Topic
from paper_radar_bot.topics import load_topics


def test_topic_arxiv_query_single_keyword():
    topic = Topic(name="Test", keywords=["LLM translation"])
    assert topic.arxiv_query == 'all:"LLM translation"'


def test_topic_arxiv_query_multiple_keywords():
    topic = Topic(name="Test", keywords=["LLM translation", "neural machine translation"])
    assert topic.arxiv_query == 'all:"LLM translation" OR all:"neural machine translation"'


def test_load_topics_from_yaml():
    yaml_content = (
        "topics:\n"
        "  - name: AI Test\n"
        "    keywords:\n"
        "      - artificial intelligence\n"
        "      - machine learning\n"
        "    max_results: 5\n"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write(yaml_content)
        path = f.name
    try:
        topics = load_topics(path)
        assert len(topics) == 1
        assert topics[0].name == "AI Test"
        assert topics[0].keywords == ["artificial intelligence", "machine learning"]
        assert topics[0].max_results == 5
    finally:
        os.unlink(path)


def test_load_topics_file_not_found_uses_fallback_query():
    topics = load_topics("nonexistent_xyz.yaml", fallback_query="cat:cs.AI")
    assert len(topics) == 1
    # keywords is empty; the raw query is carried in _override_query and returned verbatim
    assert topics[0].keywords == []
    assert topics[0].arxiv_query == "cat:cs.AI"


def test_load_topics_file_not_found_uses_defaults():
    topics = load_topics("nonexistent_xyz.yaml")
    assert len(topics) == 3
    assert all(isinstance(t, Topic) for t in topics)


def test_load_topics_skips_empty_keywords():
    yaml_content = (
        "topics:\n"
        "  - name: Valid\n"
        "    keywords:\n"
        "      - artificial intelligence\n"
        "  - name: Empty\n"
        "    keywords: []\n"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write(yaml_content)
        path = f.name
    try:
        topics = load_topics(path)
        assert len(topics) == 1
        assert topics[0].name == "Valid"
    finally:
        os.unlink(path)
