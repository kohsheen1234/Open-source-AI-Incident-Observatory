import pytest
from fastapi import HTTPException

from agentwatch.api.auth import require_api_key


def test_auth_noop_when_unset(monkeypatch):
    monkeypatch.delenv("AGENTWATCH_API_KEY", raising=False)
    from agentwatch.config import get_settings

    get_settings.cache_clear()
    require_api_key(x_api_key=None)  # must not raise


def test_auth_rejects_bad_key(monkeypatch):
    monkeypatch.setenv("AGENTWATCH_API_KEY", "secret")
    from agentwatch.config import get_settings

    get_settings.cache_clear()
    with pytest.raises(HTTPException):
        require_api_key(x_api_key="wrong")
    require_api_key(x_api_key="secret")  # correct key passes
