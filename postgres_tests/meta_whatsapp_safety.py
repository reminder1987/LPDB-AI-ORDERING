"""Local-only PostgreSQL helpers; importing this module never connects."""
import ipaddress
import os
import socket

from sqlalchemy import create_engine, delete, event, exists, select

from app.models.channel_integration_db import ChannelIntegrationDB as Channel
from app.models.provider_integration_db import ProviderIntegrationDB as Provider
from app.models.tenant_db import TenantDB as Tenant
from app.models.user_tenant_db import UserTenantDB
from app.models.payment_db import PaymentDB
from app.models.operational_incident_db import OperationalIncidentDB


def validate_server(database, address):
    if database != "lpdb_test":
        raise ValueError("Expected lpdb_test")
    try:
        local = ipaddress.ip_interface(address).ip.is_loopback
    except (ValueError, TypeError):
        local = False
    if not local:
        raise ValueError("Expected a loopback PostgreSQL server")


def local_test_url(url):
    # Reject libpq routing overrides (hostaddr, service, multi-host, etc.).
    if (url.drivername not in {"postgresql", "postgresql+psycopg2"}
            or url.database != "lpdb_test"
            or url.host not in {"localhost", "127.0.0.1", "::1"}
            or url.query):
        raise ValueError("Expected an explicit local lpdb_test URL without overrides")
    addresses = socket.getaddrinfo(url.host, url.port or 5432, type=socket.SOCK_STREAM)
    if not addresses:
        raise ValueError("No local address resolved")
    for address in addresses:
        validate_server("lpdb_test", address[4][0])
        if address[4][0] not in {"127.0.0.1", "::1"}:
            raise ValueError("Expected a canonical loopback address supported by the CLI")
    # Pin the resolved address so a later DNS lookup cannot change the target.
    return url.set(host=addresses[0][4][0])


def verify_checkout(dbapi_connection, connection_record, connection_proxy):
    try:
        with dbapi_connection.cursor() as cursor:
            cursor.execute("SELECT current_database(), inet_server_addr()::text")
            validate_server(*cursor.fetchone())
    finally:
        dbapi_connection.rollback()


def test_engine(url):
    url = local_test_url(url)
    engine = create_engine(url, connect_args={
        "hostaddr": url.host,
        "connect_timeout": 5,
        "options": "-c lock_timeout=5000 -c statement_timeout=15000",
    })
    # Validate every checkout, including workers and cleanup connections.
    event.listen(engine, "checkout", verify_checkout)
    return engine


def cli_environment(url):
    url = local_test_url(url)
    env = {key: value for key, value in os.environ.items()
           if not key.upper().startswith("PG")
           and key.upper() not in {"DATABASE_HOST", "DATABASE_PORT", "DATABASE_NAME",
                                   "DATABASE_USER", "DATABASE_PASSWORD"}}
    env.update(DATABASE_HOST=url.host, DATABASE_PORT=str(url.port or 5432),
               DATABASE_NAME="lpdb_test", DATABASE_USER=url.username or "",
               DATABASE_PASSWORD=url.password or "", PGHOSTADDR=url.host,
               PGCONNECT_TIMEOUT="5", PGOPTIONS="-c default_transaction_read_only=on -c statement_timeout=15000")
    return env


def cleanup_statements(tenants, phone_id):
    # Both the generated slug and returned ID establish fixture ownership.
    for tenant_id, slug in tenants:
        owned = select(Tenant.id).where(Tenant.id == tenant_id, Tenant.slug == slug)
        yield delete(Provider).where(
            Provider.tenant_id.in_(owned), Provider.external_id == phone_id,
            Provider.provider == "meta", Provider.integration_type == "whatsapp")
        yield delete(Channel).where(
            Channel.tenant_id.in_(owned), Channel.external_id == phone_id,
            Channel.provider == "meta", Channel.channel == "whatsapp")
        # Do not let ON DELETE CASCADE remove unrelated integrations.
        yield delete(Tenant).where(
            Tenant.id == tenant_id, Tenant.slug == slug,
            ~exists().where(Provider.tenant_id == Tenant.id),
            ~exists().where(Channel.tenant_id == Tenant.id),
            ~exists().where(UserTenantDB.tenant_id == Tenant.id),
            ~exists().where(PaymentDB.tenant_id == Tenant.id),
            ~exists().where(OperationalIncidentDB.tenant_id == Tenant.id))


def cleanup_fixtures(engine, tenants, phone_id):
    if not tenants:
        return
    with engine.begin() as connection:
        # FOR UPDATE conflicts with FK key-share locks: no related row can be
        # inserted between the ownership check and the guarded tenant deletion.
        for tenant_id, slug in tenants:
            connection.execute(select(Tenant.id).where(
                Tenant.id == tenant_id, Tenant.slug == slug).with_for_update()).all()
        for statement in cleanup_statements(tenants, phone_id):
            connection.execute(statement)
        for tenant_id, slug in tenants:
            if connection.scalar(select(Tenant.id).where(
                    Tenant.id == tenant_id, Tenant.slug == slug)) is not None:
                raise RuntimeError("Fixture retained: unexpected related records; cleanup rolled back")
