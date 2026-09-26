from decimal import Decimal

from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.api import dependencies as dependencies_api
from app.core import database as database_module
from app.main import app
from app.models.customer_db import CustomerDB
from app.models.customer_identity_db import CustomerIdentityDB
from app.models.location_db import LocationDB
from app.models.order_db import OrderDB
from app.models.tenant_db import TenantDB
from app.models.user_tenant_db import UserTenantDB
from app.services.jwt_service import create_access_token
from app.services.user_service import user_service


client = TestClient(app)


def _configure_database(monkeypatch) -> None:
    monkeypatch.setattr(
        auth_api,
        "SessionLocal",
        database_module.SessionLocal,
    )
    monkeypatch.setattr(
        dependencies_api,
        "SessionLocal",
        database_module.SessionLocal,
    )


def _ensure_tenant(
    *,
    tenant_id: int,
    slug: str,
    name: str,
) -> None:
    db = database_module.SessionLocal()

    try:
        tenant = db.get(
            TenantDB,
            tenant_id,
        )

        if tenant is None:
            db.add(
                TenantDB(
                    id=tenant_id,
                    slug=slug,
                    name=name,
                )
            )
            db.commit()

    finally:
        db.close()


def _authenticated_headers(
    monkeypatch,
    *,
    email: str,
    tenant_id: int = 1,
    tenant_slug: str = "lpdb",
    role: str = "admin",
) -> dict[str, str]:
    _configure_database(monkeypatch)

    db = database_module.SessionLocal()

    try:
        user = user_service.get_by_email(
            db,
            email,
        )

        if user is None:
            user = user_service.create_user(
                db,
                email,
                "PruebaSegura123!",
            )

        existing_access = (
            db.query(UserTenantDB)
            .filter(
                UserTenantDB.user_id == user.id,
                UserTenantDB.tenant_id == tenant_id,
            )
            .first()
        )

        if existing_access is None:
            db.add(
                UserTenantDB(
                    user_id=user.id,
                    tenant_id=tenant_id,
                    role=role,
                )
            )
        else:
            existing_access.role = role

        db.commit()

        user_id = user.id

    finally:
        db.close()

    token = create_access_token(user_id)

    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant": tenant_slug,
    }


def _ensure_location(
    *,
    tenant_id: int,
) -> int:
    if tenant_id == 1:
        return 1

    location_id = 94000 + tenant_id

    db = database_module.SessionLocal()

    try:
        location = db.get(
            LocationDB,
            location_id,
        )

        if location is None:
            db.add(
                LocationDB(
                    id=location_id,
                    tenant_id=tenant_id,
                    customer_name=(
                        f"Customer Test Location {tenant_id}"
                    ),
                    toast_name=(
                        f"Customer Test Location {tenant_id}"
                    ),
                    city="Test City",
                    address="Test Address",
                    active=True,
                )
            )
            db.commit()

        return location_id

    finally:
        db.close()


def _persist_customer(
    *,
    customer_id: int,
    tenant_id: int,
    name: str,
    phone: str | None = None,
    email: str | None = None,
    active: bool = True,
) -> None:
    db = database_module.SessionLocal()

    try:
        customer = db.get(
            CustomerDB,
            customer_id,
        )

        if customer is None:
            db.add(
                CustomerDB(
                    id=customer_id,
                    tenant_id=tenant_id,
                    name=name,
                    phone=phone,
                    email=email,
                    active=active,
                )
            )
            db.commit()
        else:
            customer.tenant_id = tenant_id
            customer.name = name
            customer.phone = phone
            customer.email = email
            customer.active = active
            db.commit()

    finally:
        db.close()


def _persist_identity(
    *,
    identity_id: int,
    tenant_id: int,
    customer_id: int,
    channel: str,
    external_id: str,
) -> None:
    db = database_module.SessionLocal()

    try:
        identity = db.get(
            CustomerIdentityDB,
            identity_id,
        )

        if identity is None:
            db.add(
                CustomerIdentityDB(
                    id=identity_id,
                    tenant_id=tenant_id,
                    customer_id=customer_id,
                    channel=channel,
                    external_id=external_id,
                )
            )
            db.commit()

    finally:
        db.close()


def _persist_order(
    *,
    order_id: int,
    tenant_id: int,
    customer_id: int,
    total: Decimal | None,
) -> None:
    location_id = _ensure_location(
        tenant_id=tenant_id,
    )

    db = database_module.SessionLocal()

    try:
        order = db.get(
            OrderDB,
            order_id,
        )

        if order is None:
            db.add(
                OrderDB(
                    id=order_id,
                    tenant_id=tenant_id,
                    customer_id=customer_id,
                    customer_name="Customer API Test",
                    location_id=location_id,
                    product="Customer API Test Product",
                    quantity=1,
                    total=total,
                )
            )
            db.commit()

    finally:
        db.close()


def test_customers_requires_authentication(
    monkeypatch,
):
    _configure_database(monkeypatch)

    response = client.get(
        "/customers",
        headers={
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code == 401


def test_customers_lists_current_tenant_only(
    monkeypatch,
):
    _ensure_tenant(
        tenant_id=2,
        slug="customers-tenant-two",
        name="Customers Tenant Two",
    )

    headers = _authenticated_headers(
        monkeypatch,
        email="customers-list@example.com",
    )

    _persist_customer(
        customer_id=95001,
        tenant_id=1,
        name="Cliente Tenant Uno",
    )

    _persist_customer(
        customer_id=95002,
        tenant_id=2,
        name="Cliente Tenant Dos",
    )

    response = client.get(
        "/customers",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    ids = {
        item["id"]
        for item in data
    }

    assert 95001 in ids
    assert 95002 not in ids


def test_customer_detail_returns_customer_and_identities(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="customers-detail@example.com",
    )

    _persist_customer(
        customer_id=95003,
        tenant_id=1,
        name="Carolina Cliente",
        phone="3055550101",
        email="carolina@example.com",
    )

    _persist_identity(
        identity_id=96001,
        tenant_id=1,
        customer_id=95003,
        channel="whatsapp",
        external_id="573055550101",
    )

    _persist_identity(
        identity_id=96002,
        tenant_id=1,
        customer_id=95003,
        channel="webchat",
        external_id="web-customer-95003",
    )

    response = client.get(
        "/customers/95003",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 95003
    assert data["name"] == "Carolina Cliente"
    assert data["phone"] == "3055550101"
    assert data["email"] == "carolina@example.com"
    assert data["active"] is True

    identities = {
        (
            identity["channel"],
            identity["external_id"],
        )
        for identity in data["identities"]
    }

    assert (
        "whatsapp",
        "573055550101",
    ) in identities

    assert (
        "webchat",
        "web-customer-95003",
    ) in identities


def test_customer_detail_blocks_cross_tenant_access(
    monkeypatch,
):
    _ensure_tenant(
        tenant_id=2,
        slug="customers-cross-tenant",
        name="Customers Cross Tenant",
    )

    headers = _authenticated_headers(
        monkeypatch,
        email="customers-cross@example.com",
    )

    _persist_customer(
        customer_id=95004,
        tenant_id=2,
        name="Cliente Secreto Tenant Dos",
    )

    response = client.get(
        "/customers/95004",
        headers=headers,
    )

    assert response.status_code == 404


def test_customers_supports_search_by_name(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="customers-search-name@example.com",
    )

    _persist_customer(
        customer_id=95005,
        tenant_id=1,
        name="Alejandra Especial",
        phone="3051111111",
        email="alejandra@example.com",
    )

    _persist_customer(
        customer_id=95006,
        tenant_id=1,
        name="Cliente Diferente",
        phone="3052222222",
        email="diferente@example.com",
    )

    response = client.get(
        "/customers?search=Alejandra",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert any(
        item["id"] == 95005
        for item in data
    )

    assert all(
        item["id"] != 95006
        for item in data
    )


def test_customers_supports_search_by_phone(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="customers-search-phone@example.com",
    )

    _persist_customer(
        customer_id=95007,
        tenant_id=1,
        name="Cliente Telefono",
        phone="3059876543",
    )

    response = client.get(
        "/customers?search=9876543",
        headers=headers,
    )

    assert response.status_code == 200

    assert any(
        item["id"] == 95007
        for item in response.json()
    )


def test_customers_supports_search_by_email(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="customers-search-email@example.com",
    )

    _persist_customer(
        customer_id=95008,
        tenant_id=1,
        name="Cliente Email",
        email="cliente.unico@example.com",
    )

    response = client.get(
        "/customers?search=cliente.unico",
        headers=headers,
    )

    assert response.status_code == 200

    assert any(
        item["id"] == 95008
        for item in response.json()
    )


def test_customers_supports_active_filter(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="customers-active-filter@example.com",
    )

    _persist_customer(
        customer_id=95009,
        tenant_id=1,
        name="Cliente Activo",
        active=True,
    )

    _persist_customer(
        customer_id=95010,
        tenant_id=1,
        name="Cliente Inactivo",
        active=False,
    )

    active_response = client.get(
        "/customers?active=true",
        headers=headers,
    )

    assert active_response.status_code == 200

    active_ids = {
        item["id"]
        for item in active_response.json()
    }

    assert 95009 in active_ids
    assert 95010 not in active_ids

    inactive_response = client.get(
        "/customers?active=false",
        headers=headers,
    )

    assert inactive_response.status_code == 200

    inactive_ids = {
        item["id"]
        for item in inactive_response.json()
    }

    assert 95010 in inactive_ids
    assert 95009 not in inactive_ids


def test_customer_summary_aggregates_orders(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="customers-orders-summary@example.com",
    )

    _persist_customer(
        customer_id=95011,
        tenant_id=1,
        name="Cliente Con Pedidos",
    )

    _persist_order(
        order_id=97001,
        tenant_id=1,
        customer_id=95011,
        total=Decimal("25.50"),
    )

    _persist_order(
        order_id=97002,
        tenant_id=1,
        customer_id=95011,
        total=Decimal("14.50"),
    )

    _persist_order(
        order_id=97003,
        tenant_id=1,
        customer_id=95011,
        total=None,
    )

    response = client.get(
        "/customers/95011",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["order_count"] == 3
    assert Decimal(
        str(data["order_total"])
    ) == Decimal("40.00")


def test_customer_list_includes_order_summary(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="customers-list-summary@example.com",
    )

    _persist_customer(
        customer_id=95012,
        tenant_id=1,
        name="Cliente Resumen Lista",
    )

    _persist_order(
        order_id=97004,
        tenant_id=1,
        customer_id=95012,
        total=Decimal("12.00"),
    )

    _persist_order(
        order_id=97005,
        tenant_id=1,
        customer_id=95012,
        total=Decimal("8.00"),
    )

    response = client.get(
        "/customers?search=Cliente%20Resumen%20Lista",
        headers=headers,
    )

    assert response.status_code == 200

    customer = next(
        item
        for item in response.json()
        if item["id"] == 95012
    )

    assert customer["order_count"] == 2
    assert Decimal(
        str(customer["order_total"])
    ) == Decimal("20.00")


def test_customer_returns_404_for_unknown_id(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="customers-not-found@example.com",
    )

    response = client.get(
        "/customers/999999999",
        headers=headers,
    )

    assert response.status_code == 404


def test_customer_rejects_non_positive_id(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="customers-invalid-id@example.com",
    )

    response = client.get(
        "/customers/0",
        headers=headers,
    )

    assert response.status_code == 422


def test_viewer_can_read_customers(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="customers-viewer@example.com",
        role="viewer",
    )

    response = client.get(
        "/customers",
        headers=headers,
    )

    assert response.status_code == 200