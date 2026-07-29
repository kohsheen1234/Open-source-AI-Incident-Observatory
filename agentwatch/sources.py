from agentwatch.collectors.base import DataSource
from agentwatch.collectors.hackernews import HackerNewsSource
from agentwatch.collectors.reddit import reddit_enabled
from agentwatch.collectors.replay import ReplaySource

# Incident-oriented searches. Generic terms ("autonomous agent") pull in mostly product
# launches and discussion; these target reports of an agent actually misbehaving, so a much
# larger share of what we collect is a real incident rather than noise.
QUERIES = [
    "AI agent deleted my files",
    "coding agent deleted my",
    "agent ignored my instructions",
    "AI agent went rogue",
    "agent ran rm -rf",
    "agent acted without permission",
    "agent leaked my",
    "agent wiped",
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


def build_provider(key: str):
    from agentwatch.classify.providers.baseline import BaselineProvider

    if key == "baseline":
        return BaselineProvider()
    if key == "majority":
        from agentwatch.classify.providers.majority import MajorityProvider

        return MajorityProvider()
    if key == "ollama":
        from agentwatch.classify.providers.ollama import OllamaProvider

        return OllamaProvider()
    raise ValueError(f"unknown provider: {key}")
