from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

from app.services.meta_whatsapp_delivery_processor import (
    MetaWhatsAppDeliveryProcessor,
)


def test_process_claimed_delivery_marks_success_as_sent():
    outbox_service = Mock()
    integration_service = Mock()
    delivery_service = Mock()

    delivery = SimpleNamespace(
        id=101,
        phone_number_id="123456789",
        recipient="15550000021",
        message="Hello from LPDB",
        claim_token="worker-success",
        attempt_count=0,
    )

    configuration = SimpleNamespace()

    integration_service.resolve.return_value = SimpleNamespace(
        configuration=configuration,
    )

    delivery_service.send_text_response.return_value = {
        "success": True,
        "message_id": "wamid.provider-101",
        "error": None,
    }

    outbox_service.mark_sent.return_value = SimpleNamespace(
        id=101,
        status="sent",
    )

    processor = MetaWhatsAppDeliveryProcessor(
        outbox_service=outbox_service,
        integration_service=integration_service,
        delivery_service=delivery_service,
    )

    result = processor.process_claimed_delivery(
        delivery=delivery,
        claim_token="worker-success",
    )

    integration_service.resolve.assert_called_once_with(
        "123456789"
    )

    delivery_service.send_text_response.assert_called_once_with(
        configuration=configuration,
        recipient="15550000021",
        message="Hello from LPDB",
    )

    outbox_service.mark_sent.assert_called_once_with(
        delivery_id=101,
        claim_token="worker-success",
        provider_message_id="wamid.provider-101",
    )

    outbox_service.mark_retryable_failure.assert_not_called()
    outbox_service.mark_failed.assert_not_called()

    assert result.status == "sent"



def test_process_claimed_delivery_schedules_retry_after():
    outbox_service = Mock()
    integration_service = Mock()
    delivery_service = Mock()

    delivery = SimpleNamespace(
        id=102,
        phone_number_id="123456789",
        recipient="15550000022",
        message="Retry from LPDB",
        claim_token="worker-retry",
        attempt_count=0,
    )

    configuration = SimpleNamespace()

    integration_service.resolve.return_value = SimpleNamespace(
        configuration=configuration,
    )

    delivery_service.send_text_response.return_value = {
        "success": False,
        "message_id": None,
        "error": "Meta rate limited request",
        "metadata": {
            "error_type": "rate_limited",
            "retryable": True,
            "status_code": 429,
            "retry_after_seconds": 45,
        },
    }

    now = datetime(
        2026,
        10,
        2,
        12,
        0,
        0,
    )

    outbox_service.mark_retryable_failure.return_value = (
        SimpleNamespace(
            id=102,
            status="pending",
        )
    )

    processor = MetaWhatsAppDeliveryProcessor(
        outbox_service=outbox_service,
        integration_service=integration_service,
        delivery_service=delivery_service,
        now_provider=lambda: now,
    )

    result = processor.process_claimed_delivery(
        delivery=delivery,
        claim_token="worker-retry",
    )

    outbox_service.mark_retryable_failure.assert_called_once_with(
        delivery_id=102,
        claim_token="worker-retry",
        error="Meta rate limited request",
        next_attempt_at=now + timedelta(seconds=45),
    )

    outbox_service.mark_sent.assert_not_called()
    outbox_service.mark_failed.assert_not_called()

    assert result.status == "pending"



def test_process_claimed_delivery_uses_exponential_backoff_without_retry_after():
    outbox_service = Mock()
    integration_service = Mock()
    delivery_service = Mock()

    delivery = SimpleNamespace(
        id=103,
        phone_number_id="123456789",
        recipient="15550000023",
        message="Temporary failure from LPDB",
        claim_token="worker-backoff",
        attempt_count=1,
    )

    configuration = SimpleNamespace()

    integration_service.resolve.return_value = SimpleNamespace(
        configuration=configuration,
    )

    delivery_service.send_text_response.return_value = {
        "success": False,
        "message_id": None,
        "error": "Meta temporary server error",
        "metadata": {
            "error_type": "server_error",
            "retryable": True,
            "status_code": 503,
        },
    }

    now = datetime(
        2026,
        10,
        2,
        12,
        0,
        0,
    )

    outbox_service.mark_retryable_failure.return_value = (
        SimpleNamespace(
            id=103,
            status="pending",
        )
    )

    processor = MetaWhatsAppDeliveryProcessor(
        outbox_service=outbox_service,
        integration_service=integration_service,
        delivery_service=delivery_service,
        now_provider=lambda: now,
    )

    result = processor.process_claimed_delivery(
        delivery=delivery,
        claim_token="worker-backoff",
    )

    outbox_service.mark_retryable_failure.assert_called_once_with(
        delivery_id=103,
        claim_token="worker-backoff",
        error="Meta temporary server error",
        next_attempt_at=now + timedelta(seconds=60),
    )

    outbox_service.mark_sent.assert_not_called()
    outbox_service.mark_failed.assert_not_called()

    assert result.status == "pending"



def test_process_claimed_delivery_marks_failed_at_max_attempts():
    outbox_service = Mock()
    integration_service = Mock()
    delivery_service = Mock()

    delivery = SimpleNamespace(
        id=104,
        phone_number_id="123456789",
        recipient="15550000024",
        message="Final attempt from LPDB",
        claim_token="worker-max-attempt",
        attempt_count=4,
    )

    configuration = SimpleNamespace()

    integration_service.resolve.return_value = SimpleNamespace(
        configuration=configuration,
    )

    delivery_service.send_text_response.return_value = {
        "success": False,
        "message_id": None,
        "error": "Meta temporary server error",
        "metadata": {
            "error_type": "server_error",
            "retryable": True,
            "status_code": 503,
            "retry_after_seconds": 45,
        },
    }

    outbox_service.mark_failed.return_value = SimpleNamespace(
        id=104,
        status="failed",
    )

    processor = MetaWhatsAppDeliveryProcessor(
        outbox_service=outbox_service,
        integration_service=integration_service,
        delivery_service=delivery_service,
    )

    result = processor.process_claimed_delivery(
        delivery=delivery,
        claim_token="worker-max-attempt",
    )

    outbox_service.mark_failed.assert_called_once_with(
        delivery_id=104,
        claim_token="worker-max-attempt",
        error="Meta temporary server error",
    )

    outbox_service.mark_retryable_failure.assert_not_called()
    outbox_service.mark_sent.assert_not_called()

    assert result.status == "failed"



def test_process_claimed_delivery_marks_nonretryable_failure():
    outbox_service = Mock()
    integration_service = Mock()
    delivery_service = Mock()

    delivery = SimpleNamespace(
        id=105,
        phone_number_id="123456789",
        recipient="15550000025",
        message="Invalid request from LPDB",
        claim_token="worker-permanent",
        attempt_count=0,
    )

    configuration = SimpleNamespace()

    integration_service.resolve.return_value = SimpleNamespace(
        configuration=configuration,
    )

    delivery_service.send_text_response.return_value = {
        "success": False,
        "message_id": None,
        "error": "Meta rejected request",
        "metadata": {
            "error_type": "http_error",
            "retryable": False,
            "status_code": 400,
        },
    }

    outbox_service.mark_failed.return_value = SimpleNamespace(
        id=105,
        status="failed",
    )

    processor = MetaWhatsAppDeliveryProcessor(
        outbox_service=outbox_service,
        integration_service=integration_service,
        delivery_service=delivery_service,
    )

    result = processor.process_claimed_delivery(
        delivery=delivery,
        claim_token="worker-permanent",
    )

    outbox_service.mark_failed.assert_called_once_with(
        delivery_id=105,
        claim_token="worker-permanent",
        error="Meta rejected request",
    )

    outbox_service.mark_retryable_failure.assert_not_called()
    outbox_service.mark_sent.assert_not_called()

    assert result.status == "failed"



def test_process_claimed_delivery_retries_integration_exception():
    outbox_service = Mock()
    integration_service = Mock()
    delivery_service = Mock()

    delivery = SimpleNamespace(
        id=106,
        phone_number_id="123456789",
        recipient="15550000026",
        message="Integration exception from LPDB",
        claim_token="worker-integration-exception",
        attempt_count=0,
    )

    integration_service.resolve.side_effect = RuntimeError(
        "Temporary integration failure"
    )

    now = datetime(
        2026,
        10,
        2,
        12,
        0,
        0,
    )

    outbox_service.mark_retryable_failure.return_value = (
        SimpleNamespace(
            id=106,
            status="pending",
        )
    )

    processor = MetaWhatsAppDeliveryProcessor(
        outbox_service=outbox_service,
        integration_service=integration_service,
        delivery_service=delivery_service,
        now_provider=lambda: now,
    )

    result = processor.process_claimed_delivery(
        delivery=delivery,
        claim_token="worker-integration-exception",
    )

    outbox_service.mark_retryable_failure.assert_called_once_with(
        delivery_id=106,
        claim_token="worker-integration-exception",
        error="Temporary integration failure",
        next_attempt_at=now + timedelta(seconds=30),
    )

    delivery_service.send_text_response.assert_not_called()
    outbox_service.mark_sent.assert_not_called()
    outbox_service.mark_failed.assert_not_called()

    assert result.status == "pending"



def test_process_claimed_delivery_retries_delivery_exception():
    outbox_service = Mock()
    integration_service = Mock()
    delivery_service = Mock()

    delivery = SimpleNamespace(
        id=107,
        phone_number_id="123456789",
        recipient="15550000027",
        message="Delivery exception from LPDB",
        claim_token="worker-delivery-exception",
        attempt_count=1,
    )

    configuration = SimpleNamespace()

    integration_service.resolve.return_value = SimpleNamespace(
        configuration=configuration,
    )

    delivery_service.send_text_response.side_effect = RuntimeError(
        "Temporary delivery failure"
    )

    now = datetime(
        2026,
        10,
        2,
        12,
        0,
        0,
    )

    outbox_service.mark_retryable_failure.return_value = (
        SimpleNamespace(
            id=107,
            status="pending",
        )
    )

    processor = MetaWhatsAppDeliveryProcessor(
        outbox_service=outbox_service,
        integration_service=integration_service,
        delivery_service=delivery_service,
        now_provider=lambda: now,
    )

    result = processor.process_claimed_delivery(
        delivery=delivery,
        claim_token="worker-delivery-exception",
    )

    integration_service.resolve.assert_called_once_with(
        "123456789"
    )

    delivery_service.send_text_response.assert_called_once_with(
        configuration=configuration,
        recipient="15550000027",
        message="Delivery exception from LPDB",
    )

    outbox_service.mark_retryable_failure.assert_called_once_with(
        delivery_id=107,
        claim_token="worker-delivery-exception",
        error="Temporary delivery failure",
        next_attempt_at=now + timedelta(seconds=60),
    )

    outbox_service.mark_sent.assert_not_called()
    outbox_service.mark_failed.assert_not_called()

    assert result.status == "pending"
