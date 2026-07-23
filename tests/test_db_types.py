from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.types import JSON

from agentwatch.db.types import JSONB


def test_jsonb_uses_postgres_jsonb_on_postgres():
    resolved = JSONB().load_dialect_impl(postgresql.dialect())
    assert isinstance(resolved, PG_JSONB)


def test_jsonb_uses_generic_json_on_sqlite():
    resolved = JSONB().load_dialect_impl(sqlite.dialect())
    assert isinstance(resolved, JSON)
