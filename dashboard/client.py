import os


class AgentWatchClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None, client=None):
        self.base_url = (
            base_url or os.environ.get("AGENTWATCH_API_URL", "http://localhost:8000")
        ).rstrip("/")
        self.api_key = api_key or os.environ.get("AGENTWATCH_API_KEY")
        if client is None:
            import httpx

            client = httpx.Client(base_url=self.base_url, timeout=30.0)
        self._client = client

    def _headers(self) -> dict:
        return {"X-API-Key": self.api_key} if self.api_key else {}

    def incidents(self, **filters) -> dict:
        params = {k: v for k, v in filters.items() if v is not None}
        return self._client.get("/incidents", params=params).json()

    def incident(self, incident_id: int) -> dict:
        return self._client.get(f"/incidents/{incident_id}").json()

    def stats(self) -> dict:
        return self._client.get("/stats").json()

    def review(
        self, incident_id: int, *, reviewer: str, decision: str, notes: str | None = None
    ) -> dict:
        resp = self._client.post(
            f"/incidents/{incident_id}/review",
            json={"reviewer": reviewer, "decision": decision, "notes": notes},
            headers=self._headers(),
        )
        return resp.json()
