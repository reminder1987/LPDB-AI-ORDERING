from decimal import Decimal

from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.api import dependencies as dependencies_api
from app.api import payments as payments_api
from app.core import database as database_module
from app.main import app
from app.models.location_db import LocationDB
from app.models.order_db import OrderDB
from app.models.payment_db import PaymentDB
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
    monkeypatch.setattr(
        payments_api,
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

    location_id = 93000 + tenant_id

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
                    customer_name=f"Payment Test Location {tenant_id}",
                    toast_name=f"Payment Test Location {tenant_id}",
                    city="Test City",
                    address="Test Address",
                    active=True,
                )
            )
            db.commit()

        return location_id

    finally:
        db.close()


def _ensure_order(
    *,
    order_id: int,
    tenant_id: int,
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
                    customer_name="Payment API Test",
                    location_id=location_id,
                    product="Payment API Test Product",
                    quantity=1,
                    total=Decimal("25.00"),
                )
            )
            db.commit()

    finally:
        db.close()


def _persist_payment(
    *,
    payment_id: int,
    tenant_id: int,
    order_id: int,
    provider: str,
    status: str,
    external_id: str | None = None,
    amount: Decimal = Decimal("25.00"),
    currency: str = "USD",
) -> None:
    _ensure_order(
        order_id=order_id,
        tenant_id=tenant_id,
    )

    db = database_module.SessionLocal()

    try:
        existing = db.get(
            PaymentDB,
            payment_id,
        )

        if existing is None:
            db.add(
                PaymentDB(
                    id=payment_id,
                    tenant_id=tenant_id,
                    order_id=order_id,
                    provider=provider,
                    external_id=external_id,
                    amount=amount,
                    currency=currency,
                    status=status,
                )
            )
            db.commit()

    finally:
        db.close()


def test_payments_requires_authentication(
    monkeypatch,
):
    _configure_database(monkeypatch)

    response = client.get(
        "/payments",
        headers={
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code == 401


def test_payments_lists_current_tenant_only(
    monkeypatch,
):
    _ensure_tenant(
        tenant_id=2,
        slug="payments-tenant-two",
        name="Payments Tenant Two",
    )

    headers = _authenticated_headers(
        monkeypatch,
        email="payments-list@example.com",
    )

    _persist_payment(
        payment_id=91001,
        tenant_id=1,
        order_id=92001,
        provider="toast",
        status="paid",
        external_id="payment-api-tenant-one",
    )

    _persist_payment(
        payment_id=91002,
        tenant_id=2,
        order_id=92002,
        provider="toast",
        status="paid",
        external_id="payment-api-tenant-two",
    )

    response = client.get(
        "/payments",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    ids = {
        item["id"]
        for item in data
    }

    assert 91001 in ids
    assert 91002 not in ids


def test_payment_detail_returns_payment(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="payments-detail@example.com",
    )

    _persist_payment(
        payment_id=91003,
        tenant_id=1,
        order_id=92003,
        provider="toast",
        status="paid",
        external_id="payment-api-detail",
        amount=Decimal("31.50"),
    )

    response = client.get(
        "/payments/91003",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 91003
    assert data["order_id"] == 92003
    assert data["provider"] == "toast"
    assert data["external_id"] == "payment-api-detail"
    assert data["status"] == "paid"
    assert Decimal(str(data["amount"])) == Decimal("31.50")
    assert data["currency"] == "USD"


def test_payment_detail_blocks_cross_tenant_access(
    monkeypatch,
):
    _ensure_tenant(
        tenant_id=2,
        slug="payments-cross-tenant",
        name="Payments Cross Tenant",
    )

    headers = _authenticated_headers(
        monkeypatch,
        email="payments-cross@example.com",
    )

    _persist_payment(
        payment_id=91004,
        tenant_id=2,
        order_id=92004,
        provider="toast",
        status="paid",
        external_id="payment-api-secret-two",
    )

    response = client.get(
        "/payments/91004",
        headers=headers,
    )

    assert response.status_code == 404


def test_payments_supports_status_and_provider_filters(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="payments-filters@example.com",
    )

    _persist_payment(
        payment_id=91005,
        tenant_id=1,
        order_id=92005,
        provider="toast",
        status="paid",
        external_id="payment-api-filter-paid",
    )

    _persist_payment(
        payment_id=91006,
        tenant_id=1,
        order_id=92006,
        provider="wompi",
        status="pending",
        external_id="payment-api-filter-pending",
    )

    response = client.get(
        "/payments?status=paid&provider=toast",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert any(
        item["id"] == 91005
        for item in data
    )

    assert all(
        item["status"] == "paid"
        and item["provider"] == "toast"
        for item in data
    )


def test_payments_normalizes_provider_filter(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="payments-provider-normalization@example.com",
    )

    _persist_payment(
        payment_id=91007,
        tenant_id=1,
        order_id=92007,
        provider="toast",
        status="paid",
        external_id="payment-api-provider-normalized",
    )

    response = client.get(
        "/payments?provider=TOAST",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert any(
        item["id"] == 91007
        for item in data
    )


def test_payments_rejects_invalid_status_filter(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="payments-invalid-status@example.com",
    )

    response = client.get(
        "/payments?status=impossible",
        headers=headers,
    )

    assert response.status_code == 422


def test_payments_rejects_empty_provider_filter(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="payments-empty-provider@example.com",
    )

    response = client.get(
        "/payments?provider=%20%20",
        headers=headers,
    )

    assert response.status_code == 422


def test_payment_returns_404_for_unknown_id(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="payments-not-found@example.com",
    )

    response = client.get(
        "/payments/999999999",
        headers=headers,
    )

    assert response.status_code == 404


def test_payment_rejects_non_positive_id(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="payments-invalid-id@example.com",
    )

    response = client.get(
        "/payments/0",
        headers=headers,
    )

    assert response.status_code == 422


def test_viewer_can_read_payments(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="payments-viewer@example.com",
        role="viewer",
    )

    response = client.get(
        "/payments",
        headers=headers,
    )

    assert response.status_code == 200