from fastapi import Depends, FastAPI, HTTPException, Query

from agentwatch.api import queries
from agentwatch.api.auth import require_api_key
from agentwatch.api.schemas import (
    ClassificationOut,
    IncidentDetail,
    IncidentSummary,
    Page,
    ReviewIn,
    ReviewOut,
    Stats,
)
from agentwatch.db.session import session_scope


def _classification_out(cls) -> ClassificationOut | None:
    if cls is None:
        return None
    return ClassificationOut(
        incident_type=cls.incident_type,
        relevance=cls.relevance,
        severity=cls.severity,
        confidence=cls.confidence,
        abstained=cls.abstained,
        model_name=cls.model_name,
        prompt_version=cls.prompt_version,
    )


def _summary(inc, cls) -> IncidentSummary:
    return IncidentSummary(
        id=inc.id,
        source=inc.source,
        url=inc.url,
        title=inc.title,
        published_at=inc.published_at,
        ingested_at=inc.ingested_at,
        classification=_classification_out(cls),
    )


def _review_out(r) -> ReviewOut:
    return ReviewOut(
        id=r.id,
        classification_id=r.classification_id,
        reviewer=r.reviewer,
        decision=r.decision,
        notes=r.notes,
        reviewed_at=r.reviewed_at,
    )


def create_app() -> FastAPI:
    app = FastAPI(title="AgentWatch API", version="0.1.0")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/incidents", response_model=Page)
    def list_incidents(
        source: str | None = None,
        incident_type: str | None = None,
        abstained: bool | None = None,
        min_severity: int | None = None,
        limit: int = Query(50, ge=1, le=500),
        offset: int = Query(0, ge=0),
    ) -> Page:
        with session_scope() as s:
            rows, total = queries.list_incidents(
                s,
                source=source,
                incident_type=incident_type,
                abstained=abstained,
                min_severity=min_severity,
                limit=limit,
                offset=offset,
            )
            items = [_summary(inc, cls) for inc, cls in rows]
        return Page(items=items, total=total, limit=limit, offset=offset)

    @app.get("/incidents/{incident_id}", response_model=IncidentDetail)
    def get_incident(incident_id: int) -> IncidentDetail:
        with session_scope() as s:
            found = queries.get_incident(s, incident_id)
            if found is None:
                raise HTTPException(status_code=404, detail="incident not found")
            inc, classes, reviews = found
            latest = classes[-1] if classes else None
            return IncidentDetail(
                **_summary(inc, latest).model_dump(),
                body=inc.body,
                classifications=[_classification_out(c) for c in classes],
                reviews=[_review_out(r) for r in reviews],
            )

    @app.post(
        "/incidents/{incident_id}/review",
        response_model=ReviewOut,
        dependencies=[Depends(require_api_key)],
    )
    def review_incident(incident_id: int, body: ReviewIn) -> ReviewOut:
        with session_scope() as s:
            try:
                r = queries.add_review(
                    s,
                    incident_id,
                    reviewer=body.reviewer,
                    decision=body.decision,
                    notes=body.notes,
                )
            except ValueError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            s.flush()
            return _review_out(r)

    @app.get("/stats", response_model=Stats)
    def get_stats() -> Stats:
        with session_scope() as s:
            return Stats(**queries.stats(s))

    @app.get("/metrics")
    def metrics():
        from fastapi import Response

        from agentwatch.metrics import render_metrics

        with session_scope() as s:
            body, content_type = render_metrics(s)
        return Response(content=body, media_type=content_type)

    @app.get("/exports/incidents.csv", dependencies=[Depends(require_api_key)])
    def export_csv():
        from fastapi.responses import PlainTextResponse

        with session_scope() as s:
            return PlainTextResponse(queries.incidents_csv(s), media_type="text/csv")

    return app
