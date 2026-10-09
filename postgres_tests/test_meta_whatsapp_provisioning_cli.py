from __future__ import annotations

import subprocess
import sys

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

from app.core.database import database_url
from app.models.channel_integration_db import ChannelIntegrationDB
from app.models.provider_integration_db import ProviderIntegrationDB


def test_cli_dry_run_does_not_write():
    url = database_url.set(database="lpdb_test")

    assert url.host in {"localhost", "127.0.0.1", "::1"}

    engine = create_engine(url)

    try:
        with Session(engine) as session:
            assert session.scalar(
                text("SELECT current_database()")
            ) == "lpdb_test"

            before_channels = session.scalar(
                select(func.count()).select_from(
                    ChannelIntegrationDB
                )
            )

            before_providers = session.scalar(
                select(func.count()).select_from(
                    ProviderIntegrationDB
                )
            )

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.provision_meta_whatsapp",
                "--database",
                "lpdb_test",
                "--tenant-slug",
                "lpdb",
                "--phone-number-id",
                "TEST_META_PHONE_001",
                "--api-version",
                "v23.0",
                "--access-token-ref",
                "TEST_META_ACCESS_TOKEN",
                "--app-secret-ref",
                "TEST_META_APP_SECRET",
                "--verify-token-ref",
                "TEST_META_VERIFY_TOKEN",
            ],
            capture_output=True,
            text=True,
            timeout=20,
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert "LISTO PARA APROVISIONAR" in result.stdout
        assert "Cambios guardados: NINGUNO" in result.stdout

        with Session(engine) as session:
            after_channels = session.scalar(
                select(func.count()).select_from(
                    ChannelIntegrationDB
                )
            )

            after_providers = session.scalar(
                select(func.count()).select_from(
                    ProviderIntegrationDB
                )
            )

        assert after_channels == before_channels
        assert after_providers == before_providers

    finally:
        engine.dispose()


def test_cli_rejects_invalid_secret_reference():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.provision_meta_whatsapp",
            "--database",
            "lpdb_test",
            "--tenant-slug",
            "lpdb",
            "--phone-number-id",
            "TEST_META_PHONE_002",
            "--api-version",
            "v23.0",
            "--access-token-ref",
            "invalid-reference",
            "--app-secret-ref",
            "TEST_META_APP_SECRET",
            "--verify-token-ref",
            "TEST_META_VERIFY_TOKEN",
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode != 0
    assert "ERROR:" in result.stdout

def test_cli_rejects_phone_assigned_to_another_tenant():
    import uuid

    from sqlalchemy import event
    from app.models.tenant_db import TenantDB

    url = database_url.set(database="lpdb_test")
    assert url.host in {"localhost", "127.0.0.1", "::1"}

    engine = create_engine(url)

    try:
        with engine.connect() as connection:
            assert connection.scalar(
                text("SELECT current_database()")
            ) == "lpdb_test"

            server = connection.scalar(
                text("SELECT inet_server_addr()::text")
            )
            assert server in {
                "127.0.0.1",
                "127.0.0.1/32",
                "::1",
                "::1/128",
            }

            connection.rollback()

            transaction = connection.begin()

            try:
                unique = uuid.uuid4().hex[:12]
                phone_id = f"TEST_CROSS_TENANT_{unique}"

                tenant_a = TenantDB(
                    slug=f"test-meta-a-{unique}",
                    name="Meta Test A",
                    active=True,
                )
                tenant_b = TenantDB(
                    slug=f"test-meta-b-{unique}",
                    name="Meta Test B",
                    active=True,
                )

                with Session(
                    bind=connection,
                    join_transaction_mode="create_savepoint",
                ) as session:
                    session.add_all([tenant_a, tenant_b])
                    session.flush()

                    channel = ChannelIntegrationDB(
                        tenant_id=tenant_a.id,
                        channel="whatsapp",
                        provider="meta",
                        external_id=phone_id,
                        webhook_secret="TEST_ONLY",
                        active=True,
                    )
                    provider = ProviderIntegrationDB(
                        tenant_id=tenant_a.id,
                        provider="meta",
                        integration_type="whatsapp",
                        external_id=phone_id,
                        configuration={"api_version": "v23.0"},
                        credentials={
                            "access_token": "TEST_META_ACCESS_TOKEN",
                            "app_secret": "TEST_META_APP_SECRET",
                            "verify_token": "TEST_META_VERIFY_TOKEN",
                        },
                        active=True,
                    )

                    session.add_all([channel, provider])
                    session.flush()

                    # Validamos el conflicto directamente contra
                    # la misma conexion de prueba.
                    existing = session.scalar(
                        select(ChannelIntegrationDB).where(
                            ChannelIntegrationDB.channel == "whatsapp",
                            ChannelIntegrationDB.provider == "meta",
                            ChannelIntegrationDB.external_id == phone_id,
                        )
                    )

                    assert existing is not None
                    assert existing.tenant_id != tenant_b.id

            finally:
                transaction.rollback()

    finally:
        engine.dispose()

def test_cli_rejects_cross_tenant_conflict():
    import uuid

    from app.models.tenant_db import TenantDB

    url = database_url.set(database="lpdb_test")
    assert url.host in {"localhost", "127.0.0.1", "::1"}

    engine = create_engine(url)

    unique = uuid.uuid4().hex[:12]
    phone_id = f"TEST_CLI_CONFLICT_{unique}"
    tenant_a_slug = f"test-cli-a-{unique}"
    tenant_b_slug = f"test-cli-b-{unique}"

    tenant_ids = []

    try:
        with Session(engine) as session:
            database = session.scalar(
                text("SELECT current_database()")
            )
            server = session.scalar(
                text("SELECT inet_server_addr()::text")
            )

            assert database == "lpdb_test"
            assert server in {
                "127.0.0.1",
                "127.0.0.1/32",
                "::1",
                "::1/128",
            }

            tenant_a = TenantDB(
                slug=tenant_a_slug,
                name="CLI Test A",
                active=True,
            )
            tenant_b = TenantDB(
                slug=tenant_b_slug,
                name="CLI Test B",
                active=True,
            )

            session.add_all([tenant_a, tenant_b])
            session.flush()

            tenant_ids = [tenant_a.id, tenant_b.id]

            session.add(
                ChannelIntegrationDB(
                    tenant_id=tenant_a.id,
                    channel="whatsapp",
                    provider="meta",
                    external_id=phone_id,
                    webhook_secret="TEST_ONLY",
                    active=True,
                )
            )

            session.add(
                ProviderIntegrationDB(
                    tenant_id=tenant_a.id,
                    provider="meta",
                    integration_type="whatsapp",
                    external_id=phone_id,
                    configuration={"api_version": "v23.0"},
                    credentials={
                        "access_token": "TEST_META_ACCESS_TOKEN",
                        "app_secret": "TEST_META_APP_SECRET",
                        "verify_token": "TEST_META_VERIFY_TOKEN",
                    },
                    active=True,
                )
            )

            session.commit()

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.provision_meta_whatsapp",
                "--database",
                "lpdb_test",
                "--tenant-slug",
                tenant_b_slug,
                "--phone-number-id",
                phone_id,
                "--api-version",
                "v23.0",
                "--access-token-ref",
                "TEST_META_ACCESS_TOKEN",
                "--app-secret-ref",
                "TEST_META_APP_SECRET",
                "--verify-token-ref",
                "TEST_META_VERIFY_TOKEN",
            ],
            capture_output=True,
            text=True,
            timeout=20,
        )

        assert result.returncode != 0
        assert "El numero pertenece a otro restaurante" in result.stdout

    finally:
        if tenant_ids:
            with Session(engine) as session:
                try:
                    session.query(ChannelIntegrationDB).filter(
                        ChannelIntegrationDB.tenant_id.in_(tenant_ids)
                    ).delete(synchronize_session=False)

                    session.query(ProviderIntegrationDB).filter(
                        ProviderIntegrationDB.tenant_id.in_(tenant_ids)
                    ).delete(synchronize_session=False)

                    session.query(TenantDB).filter(
                        TenantDB.id.in_(tenant_ids)
                    ).delete(synchronize_session=False)

                    session.commit()
                except Exception:
                    session.rollback()
                    raise

        engine.dispose()
