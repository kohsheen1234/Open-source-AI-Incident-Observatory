import argparse
from datetime import UTC, datetime, timedelta

from agentwatch.config import get_settings
from agentwatch.logging import get_logger
from agentwatch.pipeline.collect import collect_all, run_collection
from agentwatch.sources import build_default_sources, build_source
from agentwatch.storage.artifacts import ArtifactStore

log = get_logger("cli")


def _store() -> ArtifactStore:
    return ArtifactStore(get_settings().artifact_dir)


def run_once(source_key: str, since: datetime) -> int:
    return run_collection(build_source(source_key), since, store=_store())


def run_all(since: datetime) -> list[int]:
    return collect_all(build_default_sources(), since, store=_store())


def run_classify(provider_key: str, limit: int | None) -> int:
    from agentwatch.classify.persist import classify_pending
    from agentwatch.db.session import session_scope
    from agentwatch.sources import build_provider

    provider = build_provider(provider_key)
    with session_scope() as s:
        return classify_pending(s, provider, limit=limit)


def run_eval_cmd(provider_key: str) -> int:
    from agentwatch.eval.runner import run_eval
    from agentwatch.sources import build_provider

    report = run_eval(build_provider(provider_key))
    log.info(
        "eval.report",
        n=report.n,
        macro_f1=round(report.metrics.macro_f1, 3),
        abstention_rate=round(report.abstention_rate, 3),
        total_cost_usd=round(report.total_cost_usd, 4),
        avg_latency_ms=round(report.avg_latency_ms, 1),
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentwatch")
    sub = parser.add_subparsers(dest="command", required=True)

    c = sub.add_parser("collect", help="Run a one-off collection")
    c.add_argument("--source", default="all", help="replay | hackernews | all")
    c.add_argument("--since-hours", type=int, default=24 * 7)

    s = sub.add_parser("schedule", help="Run collection on a schedule")
    s.add_argument("--interval-minutes", type=int, default=60)

    cl = sub.add_parser("classify", help="Classify incidents that have no classification yet")
    cl.add_argument("--provider", default="baseline", help="baseline | ollama")
    cl.add_argument("--limit", type=int, default=None)

    ev = sub.add_parser("eval", help="Run the evaluation set and print metrics")
    ev.add_argument("--provider", default="baseline", help="baseline | ollama")

    args = parser.parse_args(argv)
    since = datetime.now(UTC) - timedelta(hours=getattr(args, "since_hours", 168))

    if args.command == "collect":
        ids = run_all(since) if args.source == "all" else [run_once(args.source, since)]
        log.info("collect.done", runs=ids)
        return 0
    if args.command == "schedule":
        from agentwatch.scheduler import build_scheduler

        build_scheduler(args.interval_minutes).start()
        return 0
    if args.command == "classify":
        n = run_classify(args.provider, args.limit)
        log.info("classify.done", classified=n)
        return 0
    if args.command == "eval":
        return run_eval_cmd(args.provider)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
