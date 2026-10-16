"""Regression checks without a PostgreSQL connection."""
from unittest.mock import MagicMock

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import URL

from postgres_tests import meta_whatsapp_safety as safety


@pytest.mark.parametrize("address", ["127.0.0.1", "127.0.0.1/32", "::1", "::1/128"])
def test_loopback_servers(address):
    safety.validate_server("lpdb_test", address)


@pytest.mark.parametrize("database,address", [
    ("postgres", "127.0.0.1"), ("lpdb", "::1"),
    ("lpdb_test", "192.0.2.1"), ("lpdb_test", "2001:db8::1"),
    ("lpdb_test", None), ("lpdb_test", "localhost"),
])
def test_reject_unverified_server(database, address):
    with pytest.raises(ValueError):
        safety.validate_server(database, address)


@pytest.mark.parametrize("changes", [
    {"host": "remote.example.invalid"}, {"database": "lpdb"},
    {"drivername": "sqlite"}, {"query": {"hostaddr": "192.0.2.1"}},
    {"query": {"service": "production"}}, {"host": None},
])
def test_url_rejected_before_connection(monkeypatch, changes):
    factory = MagicMock()
    monkeypatch.setattr(safety, "create_engine", factory)
    url = URL.create("postgresql", host="localhost", database="lpdb_test")
    with pytest.raises(ValueError):
        safety.test_engine(url._replace(**changes))
    factory.assert_not_called()


@pytest.mark.parametrize("address", ["127.0.0.1", "::1"])
def test_pin_resolution_and_subprocess_environment(monkeypatch, address):
    monkeypatch.setattr(safety.socket, "getaddrinfo", lambda *a, **k: [(0, 0, 0, "", (address, 5432))])
    monkeypatch.setenv("PGSERVICE", "untrusted")
    monkeypatch.setenv("PGHOSTADDR", "192.0.2.1")
    url = URL.create("postgresql", host="localhost", database="lpdb_test", username="test")
    assert safety.local_test_url(url).host == address
    env = safety.cli_environment(url)
    assert env["DATABASE_HOST"] == env["PGHOSTADDR"] == address
    assert env["DATABASE_NAME"] == "lpdb_test"
    assert "PGSERVICE" not in env
    assert "default_transaction_read_only=on" in env["PGOPTIONS"]


def test_remote_dns_rejected(monkeypatch):
    monkeypatch.setattr(safety.socket, "getaddrinfo", lambda *a, **k: [
        (0, 0, 0, "", ("127.0.0.1", 5432)), (0, 0, 0, "", ("192.0.2.1", 5432))])
    with pytest.raises(ValueError):
        safety.local_test_url(URL.create("postgresql", host="localhost", database="lpdb_test"))


@pytest.mark.parametrize("row", [("lpdb_test", "::1"), ("lpdb_test", "192.0.2.1"), ("lpdb", "127.0.0.1")])
def test_checkout_validates_and_ends_read_transaction(row):
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = row
    if row == ("lpdb_test", "::1"):
        safety.verify_checkout(connection, None, None)
    else:
        with pytest.raises(ValueError):
            safety.verify_checkout(connection, None, None)
    cursor.execute.assert_called_once_with("SELECT current_database(), inet_server_addr()::text")
    connection.rollback.assert_called_once_with()


def test_cleanup_is_scoped_without_executing_sql():
    statements = list(safety.cleanup_statements([(123, "unique-slug")], "unique-phone"))
    assert len(statements) == 3
    for statement in statements:
        compiled = statement.compile(dialect=postgresql.dialect())
        assert 123 in compiled.params.values()
        assert "unique-slug" in compiled.params.values()
    for statement in statements[:2]:
        compiled = statement.compile(dialect=postgresql.dialect())
        assert "unique-phone" in compiled.params.values()
        assert "meta" in compiled.params.values()
        assert "whatsapp" in compiled.params.values()
    tenant_sql = str(statements[2].compile(dialect=postgresql.dialect()))
    assert tenant_sql.count("NOT (EXISTS") == 5


def test_empty_cleanup_never_connects():
    engine = MagicMock()
    safety.cleanup_fixtures(engine, [], "unused")
    engine.begin.assert_not_called()


def test_cleanup_rolls_back_if_unexpected_records_remain():
    engine = MagicMock()
    connection = engine.begin.return_value.__enter__.return_value
    connection.scalar.return_value = 123
    with pytest.raises(RuntimeError, match="unexpected related records"):
        safety.cleanup_fixtures(engine, [(123, "unique-slug")], "unique-phone")
    assert engine.begin.return_value.__exit__.call_args.args[0] is RuntimeError


def test_engine_registers_guard_and_pins_transport(monkeypatch):
    url = URL.create("postgresql", host="::1", database="lpdb_test")
    monkeypatch.setattr(safety, "local_test_url", lambda value: value)
    factory, listen = MagicMock(), MagicMock()
    monkeypatch.setattr(safety, "create_engine", factory)
    monkeypatch.setattr(safety.event, "listen", listen)
    engine = safety.test_engine(url)
    assert factory.call_args.kwargs["connect_args"]["hostaddr"] == "::1"
    listen.assert_called_once_with(engine, "checkout", safety.verify_checkout)


def test_cleanup_failure_exits_transaction_without_partial_commit():
    engine = MagicMock()
    connection = engine.begin.return_value.__enter__.return_value
    connection.execute.side_effect = [MagicMock(), RuntimeError("simulated fixture failure")]
    with pytest.raises(RuntimeError, match="simulated fixture failure"):
        safety.cleanup_fixtures(engine, [(123, "unique-slug")], "unique-phone")
    assert connection.execute.call_count == 2
    assert engine.begin.return_value.__exit__.call_args.args[0] is RuntimeError

@pytest.mark.parametrize("driver", ["postgresql+pg8000", "postgresql+asyncpg", "postgresql+psycopg"])
def test_reject_driver_incompatible_with_libpq(monkeypatch, driver):
    factory = MagicMock()
    monkeypatch.setattr(safety, "create_engine", factory)
    with pytest.raises(ValueError):
        safety.test_engine(URL.create(driver, host="localhost", database="lpdb_test"))
    factory.assert_not_called()


@pytest.mark.parametrize("address", ["127.0.0.1", "::1"])
def test_real_settings_subprocess_overrides_dotenv(monkeypatch, address):
    import os
    from pathlib import Path
    import subprocess
    import sys

    monkeypatch.setattr(safety.socket, "getaddrinfo", lambda *a, **k: [
        (0, 0, 0, "", (address, 5432))])
    import tempfile

    # Synthetic configuration only; never open the workspace .env.
    dotenv_text = (
        "DATABASE_HOST=remote.example.invalid\nDATABASE_NAME=production\n"
        "DATABASE_PORT=6543\nDATABASE_USER=dotenv_user\n"
        "DATABASE_PASSWORD=synthetic\nJWT_SECRET_KEY=synthetic\n")
    with monkeypatch.context() as isolated:
        isolated.setattr(safety.os, "environ", {
            key: value for key, value in os.environ.items()
            if key.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP"}
        } | {"database_host": "remote.example.invalid", "PGSERVICE": "untrusted", "JWT_SECRET_KEY": "synthetic"})
        env = safety.cli_environment(URL.create(
            "postgresql+psycopg2", host="localhost", database="lpdb_test",
            username="fixture", password="synthetic"))
    config = Path(__file__).resolve().parents[1] / "app/core/config.py"
    program = (
        "import runpy,sys,os; s=runpy.run_path(sys.argv[1])['Settings'](_env_file=sys.argv[2]); "
        "assert s.database_host == os.environ['PGHOSTADDR']; "
        "assert s.database_name == 'lpdb_test'; "
        "assert s.database_port == 5432; assert s.database_user == 'fixture'; "
        "assert s.database_password == 'synthetic'; assert 'PGSERVICE' not in os.environ"
    )
    directory = Path(__file__).resolve().parent
    with tempfile.NamedTemporaryFile(mode="w", suffix=".fixture", dir=directory,
                                     delete=False) as fixture:
        fixture.write(dotenv_text)
    try:
        result = subprocess.run(
            [sys.executable, "-B", "-c", program, str(config), fixture.name],
            cwd=directory, env=env, capture_output=True, timeout=20)
        assert result.returncode == 0, "Synthetic settings subprocess failed"
    finally:
        Path(fixture.name).unlink()



def test_cleanup_guards_all_known_tenant_cascades():
    import ast
    from pathlib import Path

    sql = str(list(safety.cleanup_statements([(123, "owned")], "phone"))[-1].compile(
        dialect=postgresql.dialect()))
    # Independent discovery catches new cascade relationships omitted by cleanup.
    for path in (Path(__file__).resolve().parents[1] / "app/models").glob("*_db.py"):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        for cls in (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)):
            cascades = [node for node in ast.walk(cls) if isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Name) and node.func.id == "ForeignKey"
                        and node.args and isinstance(node.args[0], ast.Constant)
                        and node.args[0].value == "tenants.id"
                        and any(k.arg == "ondelete" and isinstance(k.value, ast.Constant)
                                and k.value.value == "CASCADE" for k in node.keywords)]
            if cascades:
                table = next(node.value.value for node in cls.body
                             if isinstance(node, ast.Assign)
                             and any(isinstance(t, ast.Name) and t.id == "__tablename__"
                                     for t in node.targets))
                assert f"FROM {table}" in sql
                assert f"{table}.tenant_id = tenants.id" in sql


def test_cleanup_locks_owned_tenant_before_mutations():
    engine = MagicMock()
    connection = engine.begin.return_value.__enter__.return_value
    connection.scalar.return_value = None
    safety.cleanup_fixtures(engine, [(123, "owned")], "phone")
    statements = [call.args[0] for call in connection.execute.call_args_list]
    first = statements[0].compile(dialect=postgresql.dialect())
    assert "FOR UPDATE" in str(first)
    assert set(first.params.values()) == {123, "owned"}
    assert all(statement.is_delete for statement in statements[1:])


def test_checkout_failure_prevents_pool_checkout():
    from sqlalchemy import event
    from sqlalchemy.pool import QueuePool

    dbapi = MagicMock()
    dbapi.cursor.return_value.__enter__.return_value.fetchone.return_value = (
        "production", "127.0.0.1")
    pool = QueuePool(lambda: dbapi)
    event.listen(pool, "checkout", safety.verify_checkout)
    with pytest.raises(ValueError):
        pool.connect()
    dbapi.rollback.assert_called_once_with()
    dbapi.close.assert_called_once_with()
    pool.dispose()


def test_real_test_modules_parse_without_importing_database():
    import ast
    from pathlib import Path

    for name in ("test_meta_whatsapp_concurrency.py", "test_meta_whatsapp_provisioning_cli.py"):
        ast.parse(Path(__file__).with_name(name).read_text(encoding="utf-8-sig"))

@pytest.mark.parametrize("address", ["127.0.0.1", "::1"])
def test_psycopg2_transport_arguments_without_connecting(monkeypatch, address):
    from psycopg2.extensions import make_dsn, parse_dsn
    from sqlalchemy.dialects.postgresql.psycopg2 import PGDialect_psycopg2

    url = URL.create("postgresql+psycopg2", host=address, database="lpdb_test",
                     username="fixture", password="synthetic")
    monkeypatch.setattr(safety, "local_test_url", lambda value: value)
    factory = MagicMock()
    monkeypatch.setattr(safety, "create_engine", factory)
    monkeypatch.setattr(safety.event, "listen", MagicMock())
    safety.test_engine(url)
    args, kwargs = PGDialect_psycopg2().create_connect_args(url)
    assert not args
    kwargs.update(factory.call_args.kwargs["connect_args"])
    parsed = parse_dsn(make_dsn(**kwargs))
    assert parsed["host"] == parsed["hostaddr"] == address
    assert parsed["dbname"] == "lpdb_test"


def test_checkout_query_error_still_rolls_back():
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.execute.side_effect = RuntimeError("query failed")
    with pytest.raises(RuntimeError, match="query failed"):
        safety.verify_checkout(connection, None, None)
    connection.rollback.assert_called_once_with()
