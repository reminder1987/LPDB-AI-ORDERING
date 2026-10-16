import threading
from uuid import uuid4

import pytest
from sqlalchemy import event, text
from sqlalchemy.orm import Session

from app.core.database import database_url
from postgres_tests.meta_whatsapp_safety import test_engine as safe_engine, cleanup_fixtures
from app.services.meta_whatsapp_provisioning_service import (
    MetaWhatsAppProvisioningError,
    MetaWhatsAppProvisioningService,
)


def test_concurrent_meta_whatsapp_provisioning():
    url = database_url.set(database="lpdb_test")

    engine = safe_engine(url)

    suffix = uuid4().hex[:12]
    phone_id = f"test-race-{suffix}"
    tenant_ids = []
    results = {}
    barrier = threading.Barrier(2, timeout=10)
    threads = []

    arguments = {
        "phone_number_id": phone_id,
        "api_version": "v-test",
        "access_token_reference": "TEST_META_ACCESS_TOKEN",
        "app_secret_reference": "TEST_META_APP_SECRET",
        "verify_token_reference": "TEST_META_VERIFY_TOKEN",
    }

    def worker(number, tenant_id):
        service = MetaWhatsAppProvisioningService()

        with Session(engine) as session:

            def synchronize_before_commit(current_session):
                if current_session is session:
                    barrier.wait()

            event.listen(
                session,
                "before_commit",
                synchronize_before_commit,
            )

            try:
                provider = service.provision(
                    session=session,
                    tenant_id=tenant_id,
                    **arguments,
                )

                results[number] = (
                    "CREADO",
                    provider.tenant_id,
                )

            except MetaWhatsAppProvisioningError as exc:
                results[number] = (
                    "RECHAZADO",
                    str(exc),
                )

            except Exception as exc:
                results[number] = (
                    "ERROR",
                    type(exc).__name__,
                    str(exc),
                )

            finally:
                event.remove(
                    session,
                    "before_commit",
                    synchronize_before_commit,
                )

    try:
        with engine.begin() as connection:
            assert connection.execute(
                text("SELECT current_database()")
            ).scalar_one() == "lpdb_test"

            for number in (1, 2):
                tenant_id = connection.execute(
                    text("""
                        INSERT INTO tenants (slug, name)
                        VALUES (:slug, :name)
                        RETURNING id
                    """),
                    {
                        "slug": f"race-{number}-{suffix}",
                        "name": f"Restaurante prueba {number}",
                    },
                ).scalar_one()

                tenant_ids.append(tenant_id)

        threads = [
            threading.Thread(
                target=worker,
                args=(number, tenant_id),
                daemon=True,
            )
            for number, tenant_id in enumerate(
                tenant_ids,
                start=1,
            )
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join(timeout=20)

        assert all(
            not thread.is_alive()
            for thread in threads
        ), "Una transaccion no finalizo."

        assert len(results) == 2, results

        created = [
            result
            for result in results.values()
            if result[0] == "CREADO"
        ]

        rejected = [
            result
            for result in results.values()
            if result[0] == "RECHAZADO"
        ]

        assert len(created) == 1, results
        assert len(rejected) == 1, results
        assert created[0][1] in tenant_ids

        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT current_database()")
            ).scalar_one() == "lpdb_test"

            channels = connection.execute(
                text("""
                    SELECT tenant_id
                    FROM channel_integrations
                    WHERE external_id = :phone_id
                """),
                {"phone_id": phone_id},
            ).scalars().all()

            providers = connection.execute(
                text("""
                    SELECT tenant_id
                    FROM provider_integrations
                    WHERE external_id = :phone_id
                """),
                {"phone_id": phone_id},
            ).scalars().all()

        assert len(channels) == 1
        assert len(providers) == 1
        assert channels[0] == providers[0]
        assert channels[0] == created[0][1]

    finally:
        # Also handle a partial Thread.start() failure or an interrupted join.
        barrier.abort()
        for thread in threads:
            if thread.ident is not None:
                thread.join(timeout=20)
        if all(not thread.is_alive() for thread in threads):
            try:
                cleanup_fixtures(
                    engine,
                    [(tenant_id, f"race-{number}-{suffix}")
                     for number, tenant_id in enumerate(tenant_ids, start=1)],
                    phone_id,
                )
            finally:
                engine.dispose()
        else:
            engine.dispose()
            pytest.fail(
                "Una transaccion sigue activa. "
                f"Se omitio la limpieza para evitar conflictos. Fixture: {suffix}; tenants: {tenant_ids}"
            )
