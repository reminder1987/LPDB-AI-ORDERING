import pytest

from app.services.toast_payment_adapter import (
    ToastPaymentAdapter,
    ToastPaymentPayloadError,
)
from app.services.toast_payment_context import (
    ToastPaymentContext,
)


def build_context(
    *,
    amount: str = "25.50",
) -> ToastPaymentContext:
    return ToastPaymentContext(
        tenant_id=1,
        payment_id=10,
        order_id=20,
        amount=amount,
        currency="USD",
        toast_order_guid="toast-order-001",
        toast_check_guid="toast-check-001",
    )


def test_builds_other_payment_payload():
    adapter = ToastPaymentAdapter(
        alternate_payment_type_guid=(
            "toast-alt-payment-001"
        ),
    )

    payload = adapter.build_payment_payload(
        build_context()
    )

    assert payload == [
        {
            "type": "OTHER",
            "amount": 25.50,
            "tipAmount": 0.0,
            "otherPayment": {
                "guid": "toast-alt-payment-001",
            },
        }
    ]


def test_payload_is_array_of_payments():
    adapter = ToastPaymentAdapter(
        alternate_payment_type_guid=(
            "toast-alt-payment-001"
        ),
    )

    payload = adapter.build_payment_payload(
        build_context()
    )

    assert isinstance(payload, list)
    assert len(payload) == 1
    assert isinstance(payload[0], dict)


def test_order_and_check_guids_are_not_in_body():
    adapter = ToastPaymentAdapter(
        alternate_payment_type_guid=(
            "toast-alt-payment-001"
        ),
    )

    payload = adapter.build_payment_payload(
        build_context()
    )

    payment = payload[0]

    assert "orderGuid" not in payment
    assert "checkGuid" not in payment


def test_normalizes_alternate_payment_guid():
    adapter = ToastPaymentAdapter(
        alternate_payment_type_guid=(
            "  toast-alt-payment-001  "
        ),
    )

    payload = adapter.build_payment_payload(
        build_context()
    )

    assert (
        payload[0]["otherPayment"]["guid"]
        == "toast-alt-payment-001"
    )


@pytest.mark.parametrize(
    "guid",
    [
        "",
        "   ",
    ],
)
def test_rejects_empty_alternate_payment_guid(
    guid,
):
    with pytest.raises(
        ToastPaymentPayloadError
    ):
        ToastPaymentAdapter(
            alternate_payment_type_guid=guid,
        )


@pytest.mark.parametrize(
    "amount",
    [
        "0",
        "0.00",
        "-1.00",
        "invalid",
    ],
)
def test_rejects_invalid_amount(amount):
    adapter = ToastPaymentAdapter(
        alternate_payment_type_guid=(
            "toast-alt-payment-001"
        ),
    )

    with pytest.raises(
        ToastPaymentPayloadError
    ):
        adapter.build_payment_payload(
            build_context(
                amount=amount,
            )
        )


def test_rejects_invalid_context():
    adapter = ToastPaymentAdapter(
        alternate_payment_type_guid=(
            "toast-alt-payment-001"
        ),
    )

    with pytest.raises(
        ToastPaymentPayloadError
    ):
        adapter.build_payment_payload(
            None
        )
