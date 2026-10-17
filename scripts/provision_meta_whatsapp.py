
"""Simulacion segura del aprovisionamiento Meta WhatsApp."""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.core.database import database_url
from app.models.channel_integration_db import ChannelIntegrationDB
from app.models.provider_integration_db import ProviderIntegrationDB
from app.models.tenant_db import TenantDB
from app.services.integration_administration_service import (
    IntegrationAdministrationService,
)
from app.services.meta_whatsapp_provisioning_service import (
    MetaWhatsAppProvisioningError,
    MetaWhatsAppProvisioningService,
)

TEST_DATABASE = "lpdb_test"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
APPLY_CONFIRMATION = "CONFIRM_LOCAL_LPDB_TEST"


def _validate_local_test_database() -> None:
    if database_url.host not in LOCAL_HOSTS:
        raise ValueError("solo se permite PostgreSQL local.")

    configured_database = getattr(database_url, "database", None)
    if configured_database is not None and configured_database != TEST_DATABASE:
        raise ValueError("La conexion no corresponde a lpdb_test.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Simular aprovisionamiento de Meta WhatsApp."
    )
    parser.add_argument("--tenant-slug", required=True)
    parser.add_argument("--phone-number-id", required=True)
    parser.add_argument("--api-version", required=True)
    parser.add_argument("--access-token-ref", required=True)
    parser.add_argument("--app-secret-ref", required=True)
    parser.add_argument("--verify-token-ref", required=True)
    parser.add_argument(
        "--database",
        required=True,
        choices=[TEST_DATABASE],
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica la integracion Meta/WhatsApp en lpdb_test local.",
    )
    parser.add_argument(
        "--confirm-apply",
        default=None,
        help="Requiere el valor exacto CONFIRM_LOCAL_LPDB_TEST para --apply.",
    )

    args = parser.parse_args()

    # El CLI permanece en dry-run por defecto; el modo --apply requiere
    # confirmacion explicita y validaciones adicionales de seguridad.
    if database_url.host not in LOCAL_HOSTS:
        print("ERROR: solo se permite PostgreSQL local.")
        return 1

    if args.database != TEST_DATABASE:
        print("ERROR: base de datos no permitida.")
        return 1

    try:
        if args.apply and (
            args.confirm_apply != APPLY_CONFIRMATION
        ):
            raise ValueError(
                "La confirmacion para --apply es obligatoria."
            )

        credentials = (
            IntegrationAdministrationService._normalize_credentials(
                {
                    "access_token": args.access_token_ref,
                    "app_secret": args.app_secret_ref,
                    "verify_token": args.verify_token_ref,
                }
            )
        )

        tenant_slug = args.tenant_slug.strip()
        phone_number_id = args.phone_number_id.strip()
        api_version = args.api_version.strip()

        if not tenant_slug or not phone_number_id or not api_version:
            raise ValueError("Hay campos obligatorios vacios.")

        test_url = database_url.set(database=TEST_DATABASE)

        engine = create_engine(
            test_url,
            pool_pre_ping=True,
        )

        try:
            with Session(engine) as session:
                connection = session.connection()

                actual_database = connection.scalar(
                    text("SELECT current_database()")
                )
                actual_host = connection.scalar(
                    text("SELECT inet_server_addr()::text")
                )

                if actual_database != TEST_DATABASE:
                    raise ValueError(
                        "La conexion no corresponde a lpdb_test."
                    )

                if actual_host not in {
                    None,
                    "127.0.0.1",
                    "127.0.0.1/32",
                    "::1",
                    "::1/128",
                }:
                    raise ValueError(
                        "El servidor PostgreSQL no es local."
                    )

                tenant = session.scalar(
                    select(TenantDB).where(
                        TenantDB.slug == tenant_slug
                    )
                )

                if tenant is None:
                    raise ValueError("El restaurante no existe.")

                if not tenant.active:
                    raise ValueError("El restaurante esta inactivo.")

                channel = session.scalar(
                    select(ChannelIntegrationDB).where(
                        ChannelIntegrationDB.channel == "whatsapp",
                        ChannelIntegrationDB.provider == "meta",
                        ChannelIntegrationDB.external_id
                        == phone_number_id,
                    )
                )

                provider = session.scalar(
                    select(ProviderIntegrationDB).where(
                        ProviderIntegrationDB.provider == "meta",
                        ProviderIntegrationDB.integration_type
                        == "whatsapp",
                        ProviderIntegrationDB.external_id
                        == phone_number_id,
                    )
                )

                if args.apply:
                    try:
                        integration = MetaWhatsAppProvisioningService().provision(
                            session=session,
                            tenant_id=tenant.id,
                            phone_number_id=phone_number_id,
                            api_version=api_version,
                            access_token_reference=args.access_token_ref,
                            app_secret_reference=args.app_secret_ref,
                            verify_token_reference=args.verify_token_ref,
                        )
                    except (MetaWhatsAppProvisioningError, ValueError):
                        session.rollback()
                        raise

                    print("META WHATSAPP - APPLY")
                    print(f"Base de datos: {actual_database}")
                    print(f"Restaurante: {tenant.name}")
                    print(f"Tenant ID: {tenant.id}")
                    print(f"Phone Number ID: {phone_number_id}")
                    print(f"API version: {api_version}")
                    print("Credenciales: referencias validadas")
                    print(f"Resultado: INTEGRACION APLICADA (ID {integration.id})")
                    print("Cambios guardados: APLICADO")
                    return 0

                if channel is not None or provider is not None:
                    if channel is None or provider is None:
                        raise ValueError(
                            "La integracion existente esta incompleta."
                        )

                    if (
                        channel.tenant_id != tenant.id
                        or provider.tenant_id != tenant.id
                    ):
                        raise ValueError(
                            "El numero pertenece a otro restaurante."
                        )

                    if not channel.active or not provider.active:
                        raise ValueError(
                            "La integracion existente esta inactiva."
                        )

                    normalized_configuration = (
                        IntegrationAdministrationService._normalize_mapping_keys(
                            provider.configuration or {},
                            field_name="configuracion",
                        )
                    )
                    normalized_credentials = (
                        IntegrationAdministrationService._normalize_mapping_keys(
                            provider.credentials or {},
                            field_name="credencial",
                        )
                    )

                    if (
                        normalized_configuration
                        != {"api_version": api_version}
                        or normalized_credentials != credentials
                    ):
                        raise ValueError(
                            "La configuracion existente es diferente."
                        )

                    result = "INTEGRACION EXISTENTE - SIN CAMBIOS"
                else:
                    result = "LISTO PARA APROVISIONAR"

                print("META WHATSAPP - DRY RUN")
                print(f"Base de datos: {actual_database}")
                print(f"Restaurante: {tenant.name}")
                print(f"Tenant ID: {tenant.id}")
                print(f"Phone Number ID: {phone_number_id}")
                print(f"API version: {api_version}")
                print("Credenciales: referencias validadas")
                print(f"Resultado: {result}")
                print("Cambios guardados: NINGUNO")

                session.rollback()

        finally:
            engine.dispose()

        return 0

    except Exception as exc:
        print(f"ERROR: {exc.__class__.__name__}: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
