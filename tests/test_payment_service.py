from decimal import Decimal

import pytest
from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.core.payment_status import (
    PAYMENT_STATUS_FAILED,
    PAYMENT_STATUS_PAID,
    PAYMENT_STATUS_PENDING,
    PAYMENT_STATUS_PROCESSING,
)
from app.models.order_db import OrderDB
from app.models.payment_db import PaymentDB
from app.models.tenant_db import TenantDB
from app.services import payment_service as payment_service_module
from app.services.payment_service import (
    PaymentDuplicateError,
    PaymentNotFoundError,
    PaymentOrderNotFoundError,
    PaymentService,
)


TEST_PROVIDERS = (
    "stripe-test",
    "wompi-test",
)


@pytest.fixture(autouse=True)
def clean_payment_test_data():
    def cleanup():
        db = SessionLocal()

        try:
            db.execute(
                delete(PaymentDB).where(
                    PaymentDB.provider.in_(TEST_PROVIDERS)
                )
            )
            db.commit()

        finally:
            db.close()

    cleanup()

    yield

    cleanup()


@pytest.fixture
def service(monkeypatch):
    monkeypatch.setattr(
        payment_service_module,
        "SessionLocal",
        SessionLocal,
    )

    return PaymentService()


def create_order(
    *,
    tenant_id: int = 1,
    customer_name: str = "Payment Test Customer",
    product: str = "Payment Test Product",
    quantity: int = 1,
) -> OrderDB:
    db = SessionLocal()

    try:
        order = OrderDB(
            tenant_id=tenant_id,
            customer_name=customer_name,
            product=product,
            quantity=quantity,
            location_id=2,
        )

        db.add(order)
        db.commit()
        db.refresh(order)
        db.expunge(order)

        return order

    finally:
        db.close()


def create_second_tenant() -> TenantDB:
    db = SessionLocal()

    try:
        existing_tenant = db.scalar(
            select(TenantDB).where(
                TenantDB.slug == "payment-tenant-two"
            )
        )

        if existing_tenant is not None:
            if not existing_tenant.active:
                existing_tenant.active = True
                db.commit()
                db.refresh(existing_tenant)

            db.expunge(existing_tenant)

            return existing_tenant

        tenant = TenantDB(
            name="Payment Tenant Two",
            slug="payment-tenant-two",
            active=True,
        )

        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        db.expunge(tenant)

        return tenant

    finally:
        db.close()


def test_create_payment(service):
    order = create_order()

    payment = service.create_payment(
        tenant_id=1,
        order_id=order.id,
        provider="stripe-test",
        amount=Decimal("25.50"),
    )

    assert payment.id is not None
    assert payment.tenant_id == 1
    assert payment.order_id == order.id
    assert payment.provider == "stripe-test"
    assert payment.amount == Decimal("25.50")
    assert payment.currency == "USD"
    assert payment.status == PAYMENT_STATUS_PENDING
    assert payment.external_id is None


def test_create_payment_normalizes_provider_and_currency(service):
    order = create_order()

    payment = service.create_payment(
        tenant_id=1,
        order_id=order.id,
        provider="  STRIPE-TEST  ",
        amount=Decimal("19.99"),
        currency=" usd ",
    )

    assert payment.provider == "stripe-test"
    assert payment.currency == "USD"


def test_create_payment_rounds_money(service):
    order = create_order()

    payment = service.create_payment(
        tenant_id=1,
        order_id=order.id,
        provider="stripe-test",
        amount=Decimal("10.555"),
    )

    assert payment.amount == Decimal("10.56")


@pytest.mark.parametrize(
    "amount",
    [
        Decimal("0"),
        Decimal("-1"),
        Decimal("-100.00"),
    ],
)
def test_create_payment_rejects_non_positive_amount(
    service,
    amount,
):
    order = create_order()

    with pytest.raises(ValueError):
        service.create_payment(
            tenant_id=1,
            order_id=order.id,
            provider="stripe-test",
            amount=amount,
        )


@pytest.mark.parametrize(
    "provider",
    [
        "",
        "   ",
    ],
)
def test_create_payment_rejects_empty_provider(
    service,
    provider,
):
    order = create_order()

    with pytest.raises(ValueError):
        service.create_payment(
            tenant_id=1,
            order_id=order.id,
            provider=provider,
            amount=Decimal("10.00"),
        )


@pytest.mark.parametrize(
    "currency",
    [
        "",
        "US",
        "USDD",
    ],
)
def test_create_payment_rejects_invalid_currency(
    service,
    currency,
):
    order = create_order()

    with pytest.raises(ValueError):
        service.create_payment(
            tenant_id=1,
            order_id=order.id,
            provider="stripe-test",
            amount=Decimal("10.00"),
            currency=currency,
        )


def test_create_payment_rejects_invalid_status(service):
    order = create_order()

    with pytest.raises(ValueError):
        service.create_payment(
            tenant_id=1,
            order_id=order.id,
            provider="stripe-test",
            amount=Decimal("10.00"),
            status="unknown",
        )


def test_create_payment_rejects_missing_order(service):
    with pytest.raises(PaymentOrderNotFoundError):
        service.create_payment(
            tenant_id=1,
            order_id=999999,
            provider="stripe-test",
            amount=Decimal("10.00"),
        )


def test_create_payment_rejects_cross_tenant_order(service):
    order = create_order()
    second_tenant = create_second_tenant()

    with pytest.raises(PaymentOrderNotFoundError):
        service.create_payment(
            tenant_id=second_tenant.id,
            order_id=order.id,
            provider="stripe-test",
            amount=Decimal("10.00"),
        )


def test_create_payment_with_external_id(service):
    order = create_order()

    payment = service.create_payment(
        tenant_id=1,
        order_id=order.id,
        provider="stripe-test",
        amount=Decimal("10.00"),
        external_id="pi_test_123",
    )

    assert payment.external_id == "pi_test_123"


def test_duplicate_external_id_is_rejected_for_same_tenant_and_provider(
    service,
):
    order = create_order()

    service.create_payment(
        tenant_id=1,
        order_id=order.id,
        provider="stripe-test",
        amount=Decimal("10.00"),
        external_id="pi_duplicate",
    )

    with pytest.raises(PaymentDuplicateError):
        service.create_payment(
            tenant_id=1,
            order_id=order.id,
            provider="stripe-test",
            amount=Decimal("10.00"),
            external_id="pi_duplicate",
        )


def test_same_external_id_can_exist_for_different_provider(service):
    order = create_order()

    stripe_payment = service.create_payment(
        tenant_id=1,
        order_id=order.id,
        provider="stripe-test",
        amount=Decimal("10.00"),
        external_id="external_123",
    )

    wompi_payment = service.create_payment(
        tenant_id=1,
        order_id=order.id,
        provider="wompi-test",
        amount=Decimal("10.00"),
        external_id="external_123",
    )

    assert stripe_payment.id != wompi_payment.id


def test_get_payment(service):
    order = create_order()

    created = service.create_payment(
        tenant_id=1,
        order_id=order.id,
        provider="stripe-test",
        amount=Decimal("10.00"),
    )

    payment = service.get_payment(
        tenant_id=1,
        payment_id=created.id,
    )

    assert payment.id == created.id
    assert payment.tenant_id == 1


def test_get_payment_rejects_wrong_tenant(service):
    order = create_order()

    created = service.create_payment(
        tenant_id=1,
        order_id=order.id,
        provider="stripe-test",
        amount=Decimal("10.00"),
    )

    second_tenant = create_second_tenant()

    with pytest.raises(PaymentNotFoundError):
        service.get_payment(
            tenant_id=second_tenant.id,
            payment_id=created.id,
        )


def test_get_payment_by_external_id(service):
    order = create_order()

    created = service.create_payment(
        tenant_id=1,
        order_id=order.id,
        provider="stripe-test",
        amount=Decimal("10.00"),
        external_id="pi_lookup",
    )

    payment = service.get_payment_by_external_id(
        tenant_id=1,
        provider="STRIPE-TEST",
        external_id="pi_lookup",
    )

    assert payment.id == created.id


def test_get_payment_by_external_id_rejects_unknown_payment(service):
    with pytest.raises(PaymentNotFoundError):
        service.get_payment_by_external_id(
            tenant_id=1,
            provider="stripe-test",
            external_id="does_not_exist",
        )


def test_attach_external_id(service):
    order = create_order()

    created = service.create_payment(
        tenant_id=1,
        order_id=order.id,
        provider="stripe-test",
        amount=Decimal("10.00"),
    )

    updated = service.attach_external_id(
        tenant_id=1,
        payment_id=created.id,
        external_id="pi_attached",
    )

    assert updated.external_id == "pi_attached"


def test_attach_external_id_rejects_duplicate(service):
    order = create_order()

    first = service.create_payment(
        tenant_id=1,
        order_id=order.id,
        provider="stripe-test",
        amount=Decimal("10.00"),
        external_id="pi_existing",
    )

    second = service.create_payment(
        tenant_id=1,
        order_id=order.id,
        provider="stripe-test",
        amount=Decimal("10.00"),
    )

    assert first.id != second.id

    with pytest.raises(PaymentDuplicateError):
        service.attach_external_id(
            tenant_id=1,
            payment_id=second.id,
            external_id="pi_existing",
        )


def test_payment_status_transition_pending_to_processing(service):
    order = create_order()

    created = service.create_payment(
        tenant_id=1,
        order_id=order.id,
        provider="stripe-test",
        amount=Decimal("10.00"),
    )

    updated = service.update_status(
        tenant_id=1,
        payment_id=created.id,
        new_status=PAYMENT_STATUS_PROCESSING,
    )

    assert updated.status == PAYMENT_STATUS_PROCESSING


def test_payment_status_transition_processing_to_paid(service):
    order = create_order()

    created = service.create_payment(
        tenant_id=1,
        order_id=order.id,
        provider="stripe-test",
        amount=Decimal("10.00"),
        status=PAYMENT_STATUS_PROCESSING,
    )

    updated = service.update_status(
        tenant_id=1,
        payment_id=created.id,
        new_status=PAYMENT_STATUS_PAID,
    )

    assert updated.status == PAYMENT_STATUS_PAID


def test_payment_status_transition_pending_to_failed(service):
    order = create_order()

    created = service.create_payment(
        tenant_id=1,
        order_id=order.id,
        provider="stripe-test",
        amount=Decimal("10.00"),
    )

    updated = service.update_status(
        tenant_id=1,
        payment_id=created.id,
        new_status=PAYMENT_STATUS_FAILED,
    )

    assert updated.status == PAYMENT_STATUS_FAILED


def test_invalid_payment_status_transition_is_rejected(service):
    order = create_order()

    created = service.create_payment(
        tenant_id=1,
        order_id=order.id,
        provider="stripe-test",
        amount=Decimal("10.00"),
        status=PAYMENT_STATUS_PAID,
    )

    with pytest.raises(ValueError):
        service.update_status(
            tenant_id=1,
            payment_id=created.id,
            new_status=PAYMENT_STATUS_PROCESSING,
        )


def test_payment_is_persisted_in_database(service):
    order = create_order()

    created = service.create_payment(
        tenant_id=1,
        order_id=order.id,
        provider="stripe-test",
        amount=Decimal("15.75"),
    )

    db = SessionLocal()

    try:
        persisted = db.get(
            PaymentDB,
            created.id,
        )

        assert persisted is not None
        assert persisted.tenant_id == 1
        assert persisted.order_id == order.id
        assert persisted.amount == Decimal("15.75")

    finally:
        db.close()