from agentwatch.collectors.base import DataSource
from agentwatch.collectors.hackernews import HackerNewsSource
from agentwatch.collectors.reddit import reddit_enabled
from agentwatch.collectors.replay import ReplaySource

QUERIES = [
    "AI agent deleted",
    "autonomous agent",
    "agent ignored instructions",
    "AI agent unexpected",
]


def build_source(key: str) -> DataSource:
    if key == "replay":
        return ReplaySource()
    if key == "hackernews":
        return HackerNewsSource(queries=QUERIES)
    raise ValueError(f"unknown source: {key}")


def build_default_sources() -> list[DataSource]:
    sources: list[DataSource] = [ReplaySource(), HackerNewsSource(queries=QUERIES)]
    # Reddit is opt-in; only included when credentials are configured.
    _ = reddit_enabled()
    return sources
