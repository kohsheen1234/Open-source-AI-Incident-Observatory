import subprocess

from sqlalchemy import create_engine, inspect


def test_migration_creates_all_tables(tmp_path, monkeypatch):
    db = tmp_path / "m.sqlite3"
    url = f"sqlite+pysqlite:///{db}"
    monkeypatch.setenv("AGENTWATCH_DATABASE_URL", url)
    result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    tables = set(inspect(create_engine(url)).get_table_names())
    assert {
        "raw_artifacts",
        "incidents",
        "classifications",
        "reviews",
        "collection_runs",
    } <= tables
