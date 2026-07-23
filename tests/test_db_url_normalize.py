from agentwatch.db.session import normalize_database_url


def test_normalizes_render_style_postgres_url():
    assert normalize_database_url("postgres://u:p@host:5432/db") == (
        "postgresql+psycopg://u:p@host:5432/db"
    )


def test_normalizes_bare_postgresql_url_to_psycopg3():
    assert normalize_database_url("postgresql://u:p@host/db") == (
        "postgresql+psycopg://u:p@host/db"
    )


def test_leaves_psycopg_and_sqlite_urls_untouched():
    assert normalize_database_url("postgresql+psycopg://u:p@host/db") == (
        "postgresql+psycopg://u:p@host/db"
    )
    assert normalize_database_url("sqlite+pysqlite:///./x.sqlite3") == (
        "sqlite+pysqlite:///./x.sqlite3"
    )
