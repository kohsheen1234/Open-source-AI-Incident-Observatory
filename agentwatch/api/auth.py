from fastapi import Header, HTTPException

from agentwatch.config import get_settings


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    configured = get_settings().api_key
    if configured and x_api_key != configured:
        raise HTTPException(status_code=401, detail="invalid or missing API key")
