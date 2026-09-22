from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import delete

from app.core.database import SessionLocal
from app.models.external_mapping_db import (
    ExternalMappingDB,
)
from app.models.order_db import OrderDB
from app.models.payment_db import PaymentDB
from app.services.external_mapping_service import (
    create_external_mapping,
)
from app.services.payment_service import (
    PaymentService,
)
from app.services.toast_payment_context import (
    ToastPaymentContextError,
    ToastPaymentContextResolver,
)


TEST_PROVIDER = "toast-payment-context-test"


def create_order() -> OrderDB:
    db = SessionLocal()

    try:
        order = OrderDB(
            tenant_id=1,
            customer_name="Toast Payment Context",
            product="Test Product",
            quantity=1,
            location_id=1,
            total=Decimal("25.50"),
        )

        db.add(order)
        db.commit()
        db.refresh(order)
        db.expunge(order)

        return order

    finally:
        db.close()


def cleanup(
    *,
    order_id: int | None = None,
) -> None:
    db = SessionLocal()

    try:
        if order_id is not None:
            db.execute(
                delete(ExternalMappingDB).where(
                    ExternalMappingDB.tenant_id == 1,
                    ExternalMappingDB.internal_id
                    == order_id,
                    ExternalMappingDB.provider == "toast",
                )
            )

            db.execute(
                delete(PaymentDB).where(
                    PaymentDB.tenant_id == 1,
                    PaymentDB.order_id == order_id,
                )
            )

            db.execute(
                delete(OrderDB).where(
                    OrderDB.id == order_id,
                    OrderDB.tenant_id == 1,
                )
            )

        db.commit()

    finally:
        db.close()


def create_payment_and_mappings():
    order = create_order()

    payment = PaymentService().create_payment(
        tenant_id=1,
        order_id=order.id,
        provider=TEST_PROVIDER,
    )

    toast_order_guid = (
        "toast-order-" + uuid4().hex
    )

    toast_check_guid = (
        "toast-check-" + uuid4().hex
    )

    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="order",
        internal_id=order.id,
        external_id=toast_order_guid,
    )

    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="check",
        internal_id=order.id,
        external_id=toast_check_guid,
    )

    return (
        order,
        payment,
        toast_order_guid,
        toast_check_guid,
    )


def test_resolves_payment_to_toast_order_and_check():
    (
        order,
        payment,
        toast_order_guid,
        toast_check_guid,
    ) = create_payment_and_mappings()

    try:
        result = ToastPaymentContextResolver().resolve(
            tenant_id=1,
            payment_id=payment.id,
        )

        assert result.tenant_id == 1
        assert result.payment_id == payment.id
        assert result.order_id == order.id
        assert result.amount == "25.50"
        assert result.currency == "USD"
        assert (
            result.toast_order_guid
            == toast_order_guid
        )
        assert (
            result.toast_check_guid
            == toast_check_guid
        )

    finally:
        cleanup(order_id=order.id)


def test_rejects_missing_toast_order_mapping():
    order = create_order()

    payment = PaymentService().create_payment(
        tenant_id=1,
        order_id=order.id,
        provider=TEST_PROVIDER,
    )

    try:
        create_external_mapping(
            tenant_id=1,
            provider="toast",
            entity_type="check",
            internal_id=order.id,
            external_id=(
                "toast-check-" + uuid4().hex
            ),
        )

        with pytest.raises(
            ToastPaymentContextError,
            match="mapping de Toast",
        ):
            ToastPaymentContextResolver().resolve(
                tenant_id=1,
                payment_id=payment.id,
            )

    finally:
        cleanup(order_id=order.id)


def test_rejects_missing_toast_check_mapping():
    order = create_order()

    payment = PaymentService().create_payment(
        tenant_id=1,
        order_id=order.id,
        provider=TEST_PROVIDER,
    )

    try:
        create_external_mapping(
            tenant_id=1,
            provider="toast",
            entity_type="order",
            internal_id=order.id,
            external_id=(
                "toast-order-" + uuid4().hex
            ),
        )

        with pytest.raises(
            ToastPaymentContextError,
            match="Toast Check",
        ):
            ToastPaymentContextResolver().resolve(
                tenant_id=1,
                payment_id=payment.id,
            )

    finally:
        cleanup(order_id=order.id)


def test_context_is_tenant_isolated():
    (
        order,
        payment,
        _,
        _,
    ) = create_payment_and_mappings()

    try:
        with pytest.raises(Exception):
            ToastPaymentContextResolver().resolve(
                tenant_id=2,
                payment_id=payment.id,
            )

    finally:
        cleanup(order_id=order.id)


def test_rejects_invalid_identifiers():
    resolver = ToastPaymentContextResolver()

    with pytest.raises(ValueError):
        resolver.resolve(
            tenant_id=0,
            payment_id=1,
        )

    with pytest.raises(ValueError):
        resolver.resolve(
            tenant_id=1,
            payment_id=0,
        )
