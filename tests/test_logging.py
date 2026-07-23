import structlog

from agentwatch.logging import configure_logging, get_logger


def test_get_logger_returns_bound_logger():
    configure_logging()
    log = get_logger("test")
    assert hasattr(log, "info")
    log.info("hello", key="value")  # must not raise


def test_configure_logging_is_idempotent():
    configure_logging()
    configure_logging()
    assert structlog.is_configured()
