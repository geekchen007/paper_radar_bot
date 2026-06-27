"""Load and parse topics.yaml into Topic records."""

import sys
from pathlib import Path

import yaml

from paper_radar_bot.models import Topic

_DEFAULT_TOPICS: list[Topic] = [
    Topic(
        name="LLM Translation",
        keywords=["LLM translation", "large language model translation", "neural machine translation"],
        max_results=10,
    ),
    Topic(
        name="Omni Model",
        keywords=["omni model", "multimodal model", "vision language model", "unified model"],
        max_results=10,
    ),
    Topic(
        name="Sign Language Translation",
        keywords=[
            "sign language translation",
            "sign language recognition",
            "gesture recognition",
            "sign language production",
        ],
        max_results=10,
    ),
]


def load_topics(topics_file: str = "topics.yaml", fallback_query: str | None = None) -> list[Topic]:
    """Load topics from YAML; fall back to fallback_query or built-in defaults if file is absent."""
    path = Path(topics_file)
    if not path.exists():
        if fallback_query is not None:
            return [Topic(name="默认领域", keywords=[], max_results=10, _override_query=fallback_query)]
        return list(_DEFAULT_TOPICS)

    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"ERROR: Failed to parse {topics_file}: {e}", file=sys.stderr)
        sys.exit(1)

    topics: list[Topic] = []
    for item in (data or {}).get("topics", []):
        keywords: list[str] = item.get("keywords", [])
        if not keywords:
            print(f"WARNING: Topic {item.get('name', '?')!r} has no keywords, skipping.", file=sys.stderr)
            continue
        topics.append(Topic(
            name=item["name"],
            keywords=keywords,
            max_results=item.get("max_results", 10),
        ))

    if not topics:
        print(f"WARNING: No valid topics found in {topics_file}, using built-in defaults.", file=sys.stderr)
        return list(_DEFAULT_TOPICS)

    return topics


def load_report_title(topics_file: str = "topics.yaml", topics: list[Topic] | None = None) -> str:
    """Load survey report title from YAML; fall back to joined topic names."""
    path = Path(topics_file)
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            print(f"ERROR: Failed to parse {topics_file}: {e}", file=sys.stderr)
            sys.exit(1)
        title = data.get("report_title")
        if title is not None and str(title).strip():
            return str(title).strip()

    if topics:
        return "与".join(t.name for t in topics)

    return "默认"
