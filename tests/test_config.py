from agentwatch.config import Settings, get_settings


def test_defaults_when_no_env(monkeypatch):
    monkeypatch.delenv("AGENTWATCH_DATABASE_URL", raising=False)
    monkeypatch.delenv("AGENTWATCH_ENVIRONMENT", raising=False)
    monkeypatch.delenv("AGENTWATCH_LOG_LEVEL", raising=False)
    s = Settings(_env_file=None)
    assert s.database_url.startswith("sqlite")
    assert s.environment == "local"
    assert s.log_level == "INFO"


def test_env_override(monkeypatch):
    monkeypatch.setenv("AGENTWATCH_DATABASE_URL", "postgresql+psycopg://u:p@db/agentwatch")
    monkeypatch.setenv("AGENTWATCH_ENVIRONMENT", "production")
    s = Settings()
    assert s.database_url == "postgresql+psycopg://u:p@db/agentwatch"
    assert s.environment == "production"


def test_get_settings_is_cached():
    assert get_settings() is get_settings()
