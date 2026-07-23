from fastapi import FastAPI

from agentwatch.cli import build_asgi_app


def test_build_asgi_app_returns_fastapi():
    assert isinstance(build_asgi_app(), FastAPI)
