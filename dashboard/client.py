import os
import time


class APIUnavailable(Exception):
    """Raised when the API cannot be reached or returns a non-JSON response."""


class AgentWatchClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None, client=None):
        self.base_url = (
            base_url or os.environ.get("AGENTWATCH_API_URL", "http://localhost:8000")
        ).rstrip("/")
        self.api_key = api_key or os.environ.get("AGENTWATCH_API_KEY")
        if client is None:
            import httpx

            client = httpx.Client(base_url=self.base_url, timeout=30.0, follow_redirects=True)
        self._client = client

    def _headers(self) -> dict:
        return {"X-API-Key": self.api_key} if self.api_key else {}

    def health(self) -> bool:
        """True if the API is up. Swallows errors so callers can poll during cold start."""
        try:
            resp = self._client.get("/health")
            return resp.status_code == 200 and resp.json().get("status") == "ok"
        except Exception:
            return False

    def wait_until_ready(self, timeout: float = 75.0, interval: float = 3.0) -> bool:
        """Poll /health until the API responds or the timeout elapses (covers cold starts)."""
        waited = 0.0
        while waited < timeout:
            if self.health():
                return True
            time.sleep(interval)
            waited += interval
        return self.health()

    def _get_json(self, path: str, params: dict | None = None, *, attempts: int = 3):
        last: Exception | None = None
        for i in range(attempts):
            try:
                resp = self._client.get(path, params=params or {})
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:  # network error, non-2xx, or non-JSON body
                last = exc
                if i < attempts - 1:
                    time.sleep(1.5 * (i + 1))
        raise APIUnavailable(str(last)) from last

    def incidents(self, **filters) -> dict:
        params = {k: v for k, v in filters.items() if v is not None}
        return self._get_json("/incidents", params)

    def incident(self, incident_id: int) -> dict:
        return self._get_json(f"/incidents/{incident_id}")

    def stats(self) -> dict:
        return self._get_json("/stats")

    def review(
        self, incident_id: int, *, reviewer: str, decision: str, notes: str | None = None
    ) -> dict:
        try:
            resp = self._client.post(
                f"/incidents/{incident_id}/review",
                json={"reviewer": reviewer, "decision": decision, "notes": notes},
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            raise APIUnavailable(str(exc)) from exc
