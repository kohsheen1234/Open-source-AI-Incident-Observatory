from sqlalchemy import create_engine, inspect

from agentwatch.db import models  # noqa: F401 - registers mappers
from agentwatch.db.base import Base


def test_all_tables_created_on_sqlite():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    tables = set(inspect(engine).get_table_names())
    assert {
        "raw_artifacts",
        "incidents",
        "classifications",
        "reviews",
        "collection_runs",
    } <= tables


def test_incident_has_author_hash_not_raw_author():
    cols = {c.name for c in models.Incident.__table__.columns}
    assert "author_hash" in cols
    assert "author" not in cols
