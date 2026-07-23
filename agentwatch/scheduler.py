from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.blocking import BlockingScheduler

from agentwatch.logging import get_logger

log = get_logger("scheduler")


def build_scheduler(interval_minutes: int) -> BlockingScheduler:
    scheduler = BlockingScheduler(timezone="UTC")

    def job() -> None:
        from agentwatch.cli import run_all

        since = datetime.now(UTC) - timedelta(minutes=interval_minutes)
        run_all(since)

    scheduler.add_job(job, "interval", minutes=interval_minutes, id="collect")
    log.info("scheduler.built", interval_minutes=interval_minutes)
    return scheduler
