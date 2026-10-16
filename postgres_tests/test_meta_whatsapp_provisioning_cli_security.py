"""CLI security checks with no PostgreSQL connections or real secrets."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy.engine import URL


@pytest.fixture
def cli_context(monkeypatch):
    # Load a private CLI module with only its database import replaced. This
    # avoids loading psycopg2 or local settings and leaves other tests intact.
    database = ModuleType("app.core.database")
    database.database_url = URL.create(
        "postgresql+psycopg2", host="127.0.0.1", database="lpdb_test",
        username="test_only", password="TEST_ONLY",
    )
    path = Path(__file__).resolve().parents[1] / "scripts" / "provision_meta_whatsapp.py"
    spec = importlib.util.spec_from_file_location("cli_security_under_test", path)
    cli = importlib.util.module_from_spec(spec)
    with monkeypatch.context() as imports:
        imports.setitem(sys.modules, "app.core.database", database)
        spec.loader.exec_module(cli)
    argv = [
        "provision_meta_whatsapp",
        "--database", "lpdb_test",
        "--tenant-slug", "test-cli-security",
        "--phone-number-id", "TEST_META_SECURITY_PHONE",
        "--api-version", "v23.0",
        "--access-token-ref", "TEST_META_ACCESS_TOKEN",
        "--app-secret-ref", "TEST_META_APP_SECRET",
        "--verify-token-ref", "TEST_META_VERIFY_TOKEN",
    ]
    monkeypatch.setattr(cli.sys, "argv", argv)
    monkeypatch.setattr(cli, "database_url", URL.create(
        "postgresql+psycopg2", host="127.0.0.1", database="lpdb_test",
        username="test_only", password="TEST_ONLY",
    ))
    engine_factory = MagicMock(name="create_engine")
    session_factory = MagicMock(name="Session")
    monkeypatch.setattr(cli, "create_engine", engine_factory)
    monkeypatch.setattr(cli, "Session", session_factory)
    session = session_factory.return_value.__enter__.return_value
    connection = session.connection.return_value
    connection.scalar.side_effect = ["lpdb_test", "127.0.0.1"]
    tenant = SimpleNamespace(id=123, active=True, name="Security test")
    channel = SimpleNamespace(tenant_id=tenant.id, active=True)
    provider = SimpleNamespace(
        tenant_id=tenant.id,
        active=True,
        configuration={"api_version": "v23.0"},
        credentials={
            "access_token": "TEST_META_ACCESS_TOKEN",
            "app_secret": "TEST_META_APP_SECRET",
            "verify_token": "TEST_META_VERIFY_TOKEN",
        },
    )
    session.scalar.side_effect = [tenant, channel, provider]
    context = SimpleNamespace(
        cli=cli, argv=argv, engine_factory=engine_factory,
        session_factory=session_factory, session=session,
        connection=connection, tenant=tenant, channel=channel,
        provider=provider,
    )
    yield context
    # Every scenario must remain a dry run, including error paths.
    for method in ("add", "add_all", "delete", "flush", "commit", "execute"):
        getattr(session, method).assert_not_called()
    connection.execute.assert_not_called()
    connection.commit.assert_not_called()


def assert_rejected(context, capsys, message):
    assert context.cli.main() == 1
    output = capsys.readouterr()
    assert output.out.strip() == f"ERROR: ValueError: {message}"
    assert output.err == ""
    context.engine_factory.return_value.dispose.assert_called_once_with()
    context.session_factory.return_value.__exit__.assert_called_once()


def test_cli_rejects_inactive_tenant(cli_context, capsys):
    cli_context.tenant.active = False

    assert_rejected(cli_context, capsys, "El restaurante esta inactivo.")

    assert cli_context.session.scalar.call_count == 1


@pytest.mark.parametrize("database", ["lpdb", "postgres", "lpdb_test_other"])
def test_cli_rejects_unauthorized_database_argument(cli_context, capsys, database):
    cli_context.argv[2] = database

    with pytest.raises(SystemExit) as exc:
        cli_context.cli.main()

    assert exc.value.code == 2
    output = capsys.readouterr()
    assert "--database: invalid choice:" in output.err
    assert database in output.err
    assert output.out == ""
    cli_context.engine_factory.assert_not_called()
    cli_context.session_factory.assert_not_called()


@pytest.mark.parametrize("host", [
    "remote.example.invalid", "192.0.2.10", "2001:db8::10", None,
])
def test_cli_rejects_remote_configured_host(cli_context, monkeypatch, capsys, host):
    monkeypatch.setattr(
        cli_context.cli, "database_url",
        cli_context.cli.database_url._replace(host=host),
    )

    assert cli_context.cli.main() == 1

    assert capsys.readouterr().out.strip() == (
        "ERROR: solo se permite PostgreSQL local."
    )
    cli_context.engine_factory.assert_not_called()
    cli_context.session_factory.assert_not_called()


@pytest.mark.parametrize("database, host, message", [
    ("lpdb", "127.0.0.1", "La conexion no corresponde a lpdb_test."),
    ("lpdb_test", "192.0.2.10", "El servidor PostgreSQL no es local."),
    ("postgres", "127.0.0.1", "La conexion no corresponde a lpdb_test."),
    ("lpdb_test", "2001:db8::10", "El servidor PostgreSQL no es local."),
])
def test_cli_rejects_unauthorized_connected_server(
    cli_context, capsys, database, host, message,
):
    cli_context.connection.scalar.side_effect = [database, host]

    assert_rejected(cli_context, capsys, message)

    cli_context.session.scalar.assert_not_called()


@pytest.mark.parametrize("missing", ["channel", "provider"])
def test_cli_rejects_incomplete_integration(cli_context, capsys, missing):
    cli_context.session.scalar.side_effect = [
        cli_context.tenant,
        None if missing == "channel" else cli_context.channel,
        None if missing == "provider" else cli_context.provider,
    ]

    assert_rejected(
        cli_context, capsys, "La integracion existente esta incompleta.",
    )


@pytest.mark.parametrize("difference", [
    "api_version", "extra_configuration", "access_token", "app_secret", "verify_token",
    "missing_api_version", "null_configuration", "missing_credentials",
    "extra_credentials", "null_credentials",
])
def test_cli_rejects_different_configuration(cli_context, capsys, difference):
    if difference == "api_version":
        cli_context.provider.configuration["api_version"] = "v22.0"
    elif difference == "extra_configuration":
        cli_context.provider.configuration["unexpected"] = "TEST_ONLY"
    elif difference == "missing_api_version":
        cli_context.provider.configuration = {}
    elif difference == "null_configuration":
        cli_context.provider.configuration = None
    elif difference == "missing_credentials":
        del cli_context.provider.credentials["verify_token"]
    elif difference == "extra_credentials":
        cli_context.provider.credentials["unexpected"] = "TEST_ONLY"
    elif difference == "null_credentials":
        cli_context.provider.credentials = None
    else:
        cli_context.provider.credentials[difference] = "TEST_OTHER_REFERENCE"

    assert_rejected(
        cli_context, capsys, "La configuracion existente es diferente.",
    )


@pytest.mark.parametrize("integration", ["channel", "provider"])
def test_cli_rejects_inactive_integration(cli_context, capsys, integration):
    getattr(cli_context, integration).active = False

    assert_rejected(
        cli_context, capsys, "La integracion existente esta inactiva.",
    )


def test_cli_accepts_matching_configuration_without_writes(cli_context, capsys):
    # Positive control: the mocks must not cause every invocation to fail.
    assert cli_context.cli.main() == 0

    output = capsys.readouterr().out
    assert "INTEGRACION EXISTENTE - SIN CAMBIOS" in output
    assert "Cambios guardados: NINGUNO" in output
    cli_context.session.rollback.assert_called_once_with()
    cli_context.engine_factory.return_value.dispose.assert_called_once_with()
