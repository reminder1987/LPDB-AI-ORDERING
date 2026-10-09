from sqlalchemy import select

from app.core import database as database_module
from app.models.channel_integration_db import ChannelIntegrationDB
from app.models.provider_integration_db import ProviderIntegrationDB
from app.services.meta_whatsapp_provisioning_service import (
    MetaWhatsAppProvisioningService,
)


def test_provision_creates_channel_and_provider_in_one_tenant():
    service = MetaWhatsAppProvisioningService()
    db = database_module.SessionLocal()

    try:
        result = service.provision(
            session=db,
            tenant_id=1,
            phone_number_id="test-meta-phone-001",
            api_version="v-test",
            access_token_reference="TEST_META_ACCESS_TOKEN",
            app_secret_reference="TEST_META_APP_SECRET",
            verify_token_reference="TEST_META_VERIFY_TOKEN",
        )

        channel = db.scalar(
            select(ChannelIntegrationDB).where(
                ChannelIntegrationDB.channel == "whatsapp",
                ChannelIntegrationDB.provider == "meta",
                ChannelIntegrationDB.external_id
                == "test-meta-phone-001",
            )
        )

        provider = db.scalar(
            select(ProviderIntegrationDB).where(
                ProviderIntegrationDB.tenant_id == 1,
                ProviderIntegrationDB.provider == "meta",
                ProviderIntegrationDB.integration_type == "whatsapp",
                ProviderIntegrationDB.external_id
                == "test-meta-phone-001",
            )
        )

        assert channel is not None
        assert provider is not None
        assert channel.tenant_id == 1
        assert provider.tenant_id == 1
        assert provider.configuration["api_version"] == "v-test"
        assert provider.credentials == {
            "access_token": "TEST_META_ACCESS_TOKEN",
            "app_secret": "TEST_META_APP_SECRET",
            "verify_token": "TEST_META_VERIFY_TOKEN",
        }
        assert result is not None

    finally:
        db.close()


def test_provision_rejects_phone_assigned_to_another_tenant():
    import pytest

    from app.models.tenant_db import TenantDB
    from app.services.meta_whatsapp_provisioning_service import (
        MetaWhatsAppProvisioningError,
    )

    service = MetaWhatsAppProvisioningService()
    db = database_module.SessionLocal()

    try:
        db.add(
            TenantDB(
                id=2,
                slug="meta-test-tenant-2",
                name="Meta Test Tenant 2",
                active=True,
            )
        )
        db.commit()

        arguments = {
            "session": db,
            "phone_number_id": "test-meta-shared-phone",
            "api_version": "v-test",
            "access_token_reference": "TEST_META_ACCESS_TOKEN",
            "app_secret_reference": "TEST_META_APP_SECRET",
            "verify_token_reference": "TEST_META_VERIFY_TOKEN",
        }

        service.provision(tenant_id=1, **arguments)

        with pytest.raises(
            MetaWhatsAppProvisioningError,
            match="ya esta asociado",
        ):
            service.provision(tenant_id=2, **arguments)

        channels = db.scalars(
            select(ChannelIntegrationDB).where(
                ChannelIntegrationDB.channel == "whatsapp",
                ChannelIntegrationDB.provider == "meta",
                ChannelIntegrationDB.external_id
                == "test-meta-shared-phone",
            )
        ).all()

        assert len(channels) == 1
        assert channels[0].tenant_id == 1

        providers = db.scalars(
            select(ProviderIntegrationDB).where(
                ProviderIntegrationDB.provider == "meta",
                ProviderIntegrationDB.integration_type == "whatsapp",
                ProviderIntegrationDB.external_id
                == "test-meta-shared-phone",
            )
        ).all()

        assert len(providers) == 1
        assert providers[0].tenant_id == 1

    finally:
        db.close()


def test_provision_is_idempotent_with_identical_configuration():
    service = MetaWhatsAppProvisioningService()
    db = database_module.SessionLocal()

    try:
        arguments = {
            "session": db,
            "tenant_id": 1,
            "phone_number_id": "test-meta-idempotent-phone",
            "api_version": "v-test",
            "access_token_reference": "TEST_META_ACCESS_TOKEN",
            "app_secret_reference": "TEST_META_APP_SECRET",
            "verify_token_reference": "TEST_META_VERIFY_TOKEN",
        }

        first = service.provision(**arguments)
        second = service.provision(**arguments)

        assert second.id == first.id

        channels = db.scalars(
            select(ChannelIntegrationDB).where(
                ChannelIntegrationDB.channel == "whatsapp",
                ChannelIntegrationDB.provider == "meta",
                ChannelIntegrationDB.external_id
                == "test-meta-idempotent-phone",
            )
        ).all()

        providers = db.scalars(
            select(ProviderIntegrationDB).where(
                ProviderIntegrationDB.tenant_id == 1,
                ProviderIntegrationDB.provider == "meta",
                ProviderIntegrationDB.integration_type == "whatsapp",
                ProviderIntegrationDB.external_id
                == "test-meta-idempotent-phone",
            )
        ).all()

        assert len(channels) == 1
        assert len(providers) == 1

    finally:
        db.close()


def test_provision_rejects_changed_configuration_without_mutation():
    import pytest

    from app.services.meta_whatsapp_provisioning_service import (
        MetaWhatsAppProvisioningError,
    )

    service = MetaWhatsAppProvisioningService()
    db = database_module.SessionLocal()

    try:
        arguments = {
            "session": db,
            "tenant_id": 1,
            "phone_number_id": "test-meta-config-conflict",
            "api_version": "v-test",
            "access_token_reference": "TEST_META_ACCESS_TOKEN",
            "app_secret_reference": "TEST_META_APP_SECRET",
            "verify_token_reference": "TEST_META_VERIFY_TOKEN",
        }

        original = service.provision(**arguments)
        original_id = original.id

        with pytest.raises(
            MetaWhatsAppProvisioningError,
            match="configuracion Meta existente es diferente",
        ):
            service.provision(
                **{
                    **arguments,
                    "access_token_reference": "DIFFERENT_META_ACCESS_TOKEN",
                }
            )

        db.expire_all()

        provider = db.scalar(
            select(ProviderIntegrationDB).where(
                ProviderIntegrationDB.id == original_id,
            )
        )

        assert provider is not None
        assert provider.credentials["access_token"] == (
            "TEST_META_ACCESS_TOKEN"
        )
        assert provider.configuration == {"api_version": "v-test"}

        channels = db.scalars(
            select(ChannelIntegrationDB).where(
                ChannelIntegrationDB.external_id
                == "test-meta-config-conflict",
                ChannelIntegrationDB.channel == "whatsapp",
                ChannelIntegrationDB.provider == "meta",
            )
        ).all()

        assert len(channels) == 1

    finally:
        db.close()


def test_provision_rolls_back_both_integrations_on_provider_failure():
    import pytest

    from sqlalchemy import event
    from sqlalchemy.exc import IntegrityError

    service = MetaWhatsAppProvisioningService()
    db = database_module.SessionLocal()
    phone_id = "test-meta-rollback-phone"

    def reject_provider_insert(mapper, connection, target):
        if target.external_id == phone_id:
            raise IntegrityError(
                "INSERT INTO provider_integrations",
                (),
                Exception("Simulated provider insert failure"),
            )

    event.listen(
        ProviderIntegrationDB,
        "before_insert",
        reject_provider_insert,
    )

    try:
        with pytest.raises(IntegrityError):
            service.provision(
                session=db,
                tenant_id=1,
                phone_number_id=phone_id,
                api_version="v-test",
                access_token_reference="TEST_META_ACCESS_TOKEN",
                app_secret_reference="TEST_META_APP_SECRET",
                verify_token_reference="TEST_META_VERIFY_TOKEN",
            )
    finally:
        event.remove(
            ProviderIntegrationDB,
            "before_insert",
            reject_provider_insert,
        )
        db.close()

    verification_db = database_module.SessionLocal()

    try:
        channels = verification_db.scalars(
            select(ChannelIntegrationDB).where(
                ChannelIntegrationDB.external_id == phone_id,
                ChannelIntegrationDB.channel == "whatsapp",
                ChannelIntegrationDB.provider == "meta",
            )
        ).all()

        providers = verification_db.scalars(
            select(ProviderIntegrationDB).where(
                ProviderIntegrationDB.external_id == phone_id,
                ProviderIntegrationDB.provider == "meta",
                ProviderIntegrationDB.integration_type == "whatsapp",
            )
        ).all()

        assert channels == []
        assert providers == []

    finally:
        verification_db.close()


def test_provision_rejects_unknown_tenant_without_writing():
    import pytest

    from app.services.meta_whatsapp_provisioning_service import (
        MetaWhatsAppProvisioningError,
    )

    service = MetaWhatsAppProvisioningService()
    db = database_module.SessionLocal()
    phone_id = "test-meta-unknown-tenant"

    try:
        with pytest.raises(
            MetaWhatsAppProvisioningError,
            match="tenant no existe o esta inactivo",
        ):
            service.provision(
                session=db,
                tenant_id=999999,
                phone_number_id=phone_id,
                api_version="v-test",
                access_token_reference="TEST_META_ACCESS_TOKEN",
                app_secret_reference="TEST_META_APP_SECRET",
                verify_token_reference="TEST_META_VERIFY_TOKEN",
            )

        channels = db.scalars(
            select(ChannelIntegrationDB).where(
                ChannelIntegrationDB.external_id == phone_id,
            )
        ).all()

        providers = db.scalars(
            select(ProviderIntegrationDB).where(
                ProviderIntegrationDB.external_id == phone_id,
            )
        ).all()

        assert channels == []
        assert providers == []

    finally:
        db.close()


def test_provision_rejects_raw_secret_without_writing():
    import pytest

    from app.services.integration_administration_service import (
        IntegrationAdministrationValidationError,
    )

    service = MetaWhatsAppProvisioningService()
    db = database_module.SessionLocal()
    phone_id = "test-meta-invalid-secret"

    try:
        with pytest.raises(
            IntegrationAdministrationValidationError,
        ):
            service.provision(
                session=db,
                tenant_id=1,
                phone_number_id=phone_id,
                api_version="v-test",
                access_token_reference="raw-secret-value",
                app_secret_reference="TEST_META_APP_SECRET",
                verify_token_reference="TEST_META_VERIFY_TOKEN",
            )

        channels = db.scalars(
            select(ChannelIntegrationDB).where(
                ChannelIntegrationDB.external_id == phone_id,
            )
        ).all()

        providers = db.scalars(
            select(ProviderIntegrationDB).where(
                ProviderIntegrationDB.external_id == phone_id,
            )
        ).all()

        assert channels == []
        assert providers == []

    finally:
        db.close()


def test_provision_rejects_incomplete_integration_without_mutation():
    import pytest

    from app.services.meta_whatsapp_provisioning_service import (
        MetaWhatsAppProvisioningError,
    )

    service = MetaWhatsAppProvisioningService()
    db = database_module.SessionLocal()
    phone_id = "test-meta-incomplete-phone"

    try:
        channel = ChannelIntegrationDB(
            tenant_id=1,
            channel="whatsapp",
            provider="meta",
            external_id=phone_id,
            webhook_secret="TEST_WEBHOOK_SECRET",
            active=True,
        )
        db.add(channel)
        db.commit()
        channel_id = channel.id

        with pytest.raises(
            MetaWhatsAppProvisioningError,
            match="integracion Meta existente esta incompleta",
        ):
            service.provision(
                session=db,
                tenant_id=1,
                phone_number_id=phone_id,
                api_version="v-test",
                access_token_reference="TEST_META_ACCESS_TOKEN",
                app_secret_reference="TEST_META_APP_SECRET",
                verify_token_reference="TEST_META_VERIFY_TOKEN",
            )

        db.expire_all()

        saved_channel = db.get(ChannelIntegrationDB, channel_id)

        assert saved_channel is not None
        assert saved_channel.tenant_id == 1
        assert saved_channel.active is True
        assert saved_channel.webhook_secret == "TEST_WEBHOOK_SECRET"

        providers = db.scalars(
            select(ProviderIntegrationDB).where(
                ProviderIntegrationDB.external_id == phone_id,
                ProviderIntegrationDB.provider == "meta",
                ProviderIntegrationDB.integration_type == "whatsapp",
            )
        ).all()

        assert providers == []

    finally:
        db.close()


def test_provision_rejects_provider_without_channel():
    import pytest

    from app.services.meta_whatsapp_provisioning_service import (
        MetaWhatsAppProvisioningError,
    )

    service = MetaWhatsAppProvisioningService()
    db = database_module.SessionLocal()
    phone_id = "test-meta-provider-only"

    credentials = {
        "access_token": "TEST_META_ACCESS_TOKEN",
        "app_secret": "TEST_META_APP_SECRET",
        "verify_token": "TEST_META_VERIFY_TOKEN",
    }

    try:
        provider = ProviderIntegrationDB(
            tenant_id=1,
            provider="meta",
            integration_type="whatsapp",
            external_id=phone_id,
            configuration={"api_version": "v-test"},
            credentials=credentials,
            active=True,
        )
        db.add(provider)
        db.commit()
        provider_id = provider.id

        with pytest.raises(
            MetaWhatsAppProvisioningError,
            match="integracion Meta existente esta incompleta",
        ):
            service.provision(
                session=db,
                tenant_id=1,
                phone_number_id=phone_id,
                api_version="v-test",
                access_token_reference="TEST_META_ACCESS_TOKEN",
                app_secret_reference="TEST_META_APP_SECRET",
                verify_token_reference="TEST_META_VERIFY_TOKEN",
            )

        db.expire_all()

        saved_provider = db.get(
            ProviderIntegrationDB,
            provider_id,
        )

        assert saved_provider is not None
        assert saved_provider.tenant_id == 1
        assert saved_provider.credentials == credentials

        channels = db.scalars(
            select(ChannelIntegrationDB).where(
                ChannelIntegrationDB.external_id == phone_id,
                ChannelIntegrationDB.channel == "whatsapp",
                ChannelIntegrationDB.provider == "meta",
            )
        ).all()

        assert channels == []

    finally:
        db.close()


def test_provision_rejects_inactive_integration_without_reactivation():
    import pytest

    from app.services.meta_whatsapp_provisioning_service import (
        MetaWhatsAppProvisioningError,
    )

    service = MetaWhatsAppProvisioningService()
    db = database_module.SessionLocal()
    phone_id = "test-meta-inactive-phone"

    arguments = {
        "session": db,
        "tenant_id": 1,
        "phone_number_id": phone_id,
        "api_version": "v-test",
        "access_token_reference": "TEST_META_ACCESS_TOKEN",
        "app_secret_reference": "TEST_META_APP_SECRET",
        "verify_token_reference": "TEST_META_VERIFY_TOKEN",
    }

    try:
        provider = service.provision(**arguments)

        channel = db.scalar(
            select(ChannelIntegrationDB).where(
                ChannelIntegrationDB.channel == "whatsapp",
                ChannelIntegrationDB.provider == "meta",
                ChannelIntegrationDB.external_id == phone_id,
            )
        )

        channel.active = False
        provider.active = False
        db.commit()

        with pytest.raises(
            MetaWhatsAppProvisioningError,
            match="integracion Meta existente esta inactiva",
        ):
            service.provision(**arguments)

        db.expire_all()

        assert db.get(ChannelIntegrationDB, channel.id).active is False
        assert db.get(ProviderIntegrationDB, provider.id).active is False

    finally:
        db.close()


def test_provisioned_meta_integration_resolves_configuration(monkeypatch):
    from app.services.meta_whatsapp_integration_service import (
        MetaWhatsAppIntegrationService,
    )
    from app.services.meta_whatsapp_configuration_service import (
        MetaWhatsAppConfigurationService,
    )
    from app.services.integration_secret_service import IntegrationSecretService
    from app.services.channel_integration_service import ChannelIntegrationService
    from app.services.provider_integration_service import ProviderIntegrationService
    from app.core import database as database_module

    import app.services.channel_integration_service as channel_module
    import app.services.provider_integration_service as provider_module

    monkeypatch.setattr(
        channel_module,
        "SessionLocal",
        database_module.SessionLocal,
    )
    monkeypatch.setattr(
        provider_module,
        "SessionLocal",
        database_module.SessionLocal,
    )

    environment = {
        "TEST_META_ACCESS_TOKEN": "fake-access-token",
        "TEST_META_APP_SECRET": "fake-app-secret",
        "TEST_META_VERIFY_TOKEN": "fake-verify-token",
    }

    service = MetaWhatsAppProvisioningService()
    db = database_module.SessionLocal()
    phone_id = "test-meta-end-to-end-phone"

    try:
        service.provision(
            session=db,
            tenant_id=1,
            phone_number_id=phone_id,
            api_version="v-test",
            access_token_reference="TEST_META_ACCESS_TOKEN",
            app_secret_reference="TEST_META_APP_SECRET",
            verify_token_reference="TEST_META_VERIFY_TOKEN",
        )
    finally:
        db.close()

    resolver = MetaWhatsAppIntegrationService(
        channel_service=ChannelIntegrationService(),
        provider_service=ProviderIntegrationService(),
        configuration_service=MetaWhatsAppConfigurationService(
            secret_service=IntegrationSecretService(environment=environment)
        ),
    )

    integration = resolver.resolve(phone_id)

    assert integration.channel_integration.tenant_id == 1
    assert integration.provider_integration.tenant_id == 1
    assert integration.configuration.phone_number_id == phone_id
    assert integration.configuration.api_version == "v-test"
    assert integration.configuration.access_token == "fake-access-token"
    assert integration.configuration.app_secret == "fake-app-secret"
    assert integration.configuration.verify_token == "fake-verify-token"


def test_provision_handles_database_unique_conflict():
    import pytest

    from sqlalchemy import event
    from sqlalchemy.exc import IntegrityError

    from app.services.meta_whatsapp_provisioning_service import (
        MetaWhatsAppProvisioningError,
    )

    service = MetaWhatsAppProvisioningService()
    db = database_module.SessionLocal()
    phone_id = "test-meta-concurrent-conflict"

    def simulate_unique_conflict(mapper, connection, target):
        if target.external_id == phone_id:
            raise IntegrityError(
                "INSERT INTO channel_integrations",
                (),
                Exception("uq_channel_integration_external"),
            )

    event.listen(
        ChannelIntegrationDB,
        "before_insert",
        simulate_unique_conflict,
    )

    try:
        with pytest.raises(MetaWhatsAppProvisioningError):
            service.provision(
                session=db,
                tenant_id=1,
                phone_number_id=phone_id,
                api_version="v-test",
                access_token_reference="TEST_META_ACCESS_TOKEN",
                app_secret_reference="TEST_META_APP_SECRET",
                verify_token_reference="TEST_META_VERIFY_TOKEN",
            )
    finally:
        event.remove(
            ChannelIntegrationDB,
            "before_insert",
            simulate_unique_conflict,
        )
        db.close()


def test_provision_handles_postgresql_unique_violation():
    import pytest

    from sqlalchemy import event
    from sqlalchemy.exc import IntegrityError

    from app.services.meta_whatsapp_provisioning_service import (
        MetaWhatsAppProvisioningError,
    )

    service = MetaWhatsAppProvisioningService()
    db = database_module.SessionLocal()
    phone_id = "test-meta-postgresql-conflict"

    class FakePostgresError(Exception):
        sqlstate = "23505"
        constraint_name = "uq_channel_integration_external"

        def __str__(self):
            return "duplicate key value violates unique constraint"

    def simulate_postgresql_conflict(mapper, connection, target):
        if target.external_id == phone_id:
            raise IntegrityError(
                "INSERT INTO channel_integrations",
                (),
                FakePostgresError(),
            )

    event.listen(
        ChannelIntegrationDB,
        "before_insert",
        simulate_postgresql_conflict,
    )

    try:
        with pytest.raises(MetaWhatsAppProvisioningError):
            service.provision(
                session=db,
                tenant_id=1,
                phone_number_id=phone_id,
                api_version="v-test",
                access_token_reference="TEST_META_ACCESS_TOKEN",
                app_secret_reference="TEST_META_APP_SECRET",
                verify_token_reference="TEST_META_VERIFY_TOKEN",
            )
    finally:
        event.remove(
            ChannelIntegrationDB,
            "before_insert",
            simulate_postgresql_conflict,
        )
        db.close()


def test_provision_preserves_unrelated_integrity_errors():
    import pytest

    from sqlalchemy import event
    from sqlalchemy.exc import IntegrityError

    service = MetaWhatsAppProvisioningService()
    db = database_module.SessionLocal()
    phone_id = "test-meta-unrelated-integrity"

    class FakeForeignKeyError(Exception):
        sqlstate = "23503"
        constraint_name = "fk_unrelated"

        def __str__(self):
            return "foreign key violation"

    def simulate_foreign_key_failure(mapper, connection, target):
        if target.external_id == phone_id:
            raise IntegrityError(
                "INSERT INTO channel_integrations",
                (),
                FakeForeignKeyError(),
            )

    event.listen(
        ChannelIntegrationDB,
        "before_insert",
        simulate_foreign_key_failure,
    )

    try:
        with pytest.raises(IntegrityError):
            service.provision(
                session=db,
                tenant_id=1,
                phone_number_id=phone_id,
                api_version="v-test",
                access_token_reference="TEST_META_ACCESS_TOKEN",
                app_secret_reference="TEST_META_APP_SECRET",
                verify_token_reference="TEST_META_VERIFY_TOKEN",
            )

        assert db.scalar(
            select(ChannelIntegrationDB).where(
                ChannelIntegrationDB.external_id == phone_id,
            )
        ) is None

        assert db.scalar(
            select(ProviderIntegrationDB).where(
                ProviderIntegrationDB.external_id == phone_id,
            )
        ) is None

    finally:
        event.remove(
            ChannelIntegrationDB,
            "before_insert",
            simulate_foreign_key_failure,
        )
        db.close()
