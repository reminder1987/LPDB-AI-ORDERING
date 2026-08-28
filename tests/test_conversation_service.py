from app.core.tenant_context import TenantContext
from app.services.conversation_service import (
    ConversationService,
    ConversationState,
)


TENANT_LPDB = TenantContext(
    tenant_id=1,
    tenant_slug="lpdb",
    tenant_name="Los Perritos Del Barrio",
)


def test_save_and_get_state_preserves_tenant_session():
    service = ConversationService()

    state = ConversationState(
        status="ready",
        customer_name="Carolina",
        location_id=1,
    )

    session_id = "conversation-persistence-1"

    service._save_state(
        session_id=session_id,
        state=state,
        tenant_id=TENANT_LPDB.tenant_id,
    )

    recovered = service.get_state(
        session_id=session_id,
        tenant_id=TENANT_LPDB.tenant_id,
    )

    assert recovered.status == "ready"
    assert recovered.customer_name == "Carolina"
    assert recovered.location_id == 1

    service._clear_state(
        session_id=session_id,
        tenant_id=TENANT_LPDB.tenant_id,
    )


def test_get_state_does_not_cross_tenant_boundary():
    service = ConversationService()

    session_id = "conversation-tenant-isolation-1"

    state = ConversationState(
        status="ready",
        customer_name="Carolina",
        location_id=1,
    )

    service._save_state(
        session_id=session_id,
        state=state,
        tenant_id=TENANT_LPDB.tenant_id,
    )

    isolated = service.get_state(
        session_id=session_id,
        tenant_id=999999,
    )

    assert isolated.status == "new"
    assert isolated.customer_name is None
    assert isolated.location_id is None

    service._clear_state(
        session_id=session_id,
        tenant_id=TENANT_LPDB.tenant_id,
    )


def test_clear_state_removes_only_matching_tenant_session():
    service = ConversationService()

    session_id = "conversation-clear-1"

    state = ConversationState(
        status="ready",
        customer_name="Carolina",
        location_id=1,
    )

    service._save_state(
        session_id=session_id,
        state=state,
        tenant_id=TENANT_LPDB.tenant_id,
    )

    service._clear_state(
        session_id=session_id,
        tenant_id=TENANT_LPDB.tenant_id,
    )

    recovered = service.get_state(
        session_id=session_id,
        tenant_id=TENANT_LPDB.tenant_id,
    )

    assert recovered.status == "new"
    assert recovered.items == []
    assert recovered.customer_name is None
    assert recovered.location_id is None


def test_missing_session_returns_new_state():
    service = ConversationService()

    state = service.get_state(
        session_id="conversation-does-not-exist",
        tenant_id=TENANT_LPDB.tenant_id,
    )

    assert state.status == "new"
    assert state.items == []
    assert state.customer_name is None
    assert state.location_id is None


def test_same_session_id_recovers_conversation_state():
    service = ConversationService()

    session_id = "conversation-multi-turn-1"

    first_turn_state = ConversationState(
        status="waiting_combo_confirmation",
        customer_name="Carolina",
        location_id=1,
        combo_product="PERRO DEL BARRIO",
    )

    service._save_state(
        session_id=session_id,
        state=first_turn_state,
        tenant_id=TENANT_LPDB.tenant_id,
    )

    second_turn_state = service.get_state(
        session_id=session_id,
        tenant_id=TENANT_LPDB.tenant_id,
    )

    assert second_turn_state.status == (
        "waiting_combo_confirmation"
    )

    assert second_turn_state.customer_name == (
        "Carolina"
    )

    assert second_turn_state.location_id == 1

    assert second_turn_state.combo_product == (
        "PERRO DEL BARRIO"
    )

    service._clear_state(
        session_id=session_id,
        tenant_id=TENANT_LPDB.tenant_id,
    )


def test_multi_turn_conversation_uses_persisted_state():
    service = ConversationService()

    session_id = "conversation-real-multi-turn-1"

    first_state = ConversationState(
        status="waiting_combo_confirmation",
        customer_name="Carolina",
        location_id=1,
        combo_product="PERRO DEL BARRIO",
    )

    service._save_state(
        session_id=session_id,
        state=first_state,
        tenant_id=TENANT_LPDB.tenant_id,
    )

    recovered_state = service.get_state(
        session_id=session_id,
        tenant_id=TENANT_LPDB.tenant_id,
    )

    assert recovered_state.status == (
        "waiting_combo_confirmation"
    )

    assert recovered_state.combo_product == (
        "PERRO DEL BARRIO"
    )

    assert recovered_state.customer_name == (
        "Carolina"
    )

    assert recovered_state.location_id == 1

    recovered_state.status = "waiting_beverage"
    recovered_state.combo_requested = True
    recovered_state.beverage_required = True

    service._save_state(
        session_id=session_id,
        state=recovered_state,
        tenant_id=TENANT_LPDB.tenant_id,
    )

    second_turn_state = service.get_state(
        session_id=session_id,
        tenant_id=TENANT_LPDB.tenant_id,
    )

    assert second_turn_state.status == (
        "waiting_beverage"
    )

    assert second_turn_state.combo_requested is True

    assert second_turn_state.beverage_required is True

    assert second_turn_state.combo_product == (
        "PERRO DEL BARRIO"
    )

    assert second_turn_state.customer_name == (
        "Carolina"
    )

    assert second_turn_state.location_id == 1

    service._clear_state(
        session_id=session_id,
        tenant_id=TENANT_LPDB.tenant_id,
    )

def test_save_and_get_openai_response_id_preserves_tenant_session():
    service = ConversationService()

    session_id = "openai-response-persistence-1"

    service.save_openai_response_id(
        session_id=session_id,
        tenant_id=TENANT_LPDB.tenant_id,
        response_id="response_test_123",
    )

    recovered = service.get_openai_response_id(
        session_id=session_id,
        tenant_id=TENANT_LPDB.tenant_id,
    )

    assert recovered == "response_test_123"

    service._clear_state(
        session_id=session_id,
        tenant_id=TENANT_LPDB.tenant_id,
    )


def test_get_openai_response_id_does_not_cross_tenant_boundary():
    service = ConversationService()

    session_id = "openai-response-tenant-isolation-1"

    service.save_openai_response_id(
        session_id=session_id,
        tenant_id=TENANT_LPDB.tenant_id,
        response_id="response_private_123",
    )

    isolated = service.get_openai_response_id(
        session_id=session_id,
        tenant_id=999999,
    )

    assert isolated is None

    service._clear_state(
        session_id=session_id,
        tenant_id=TENANT_LPDB.tenant_id,
    )


def test_save_openai_response_id_updates_existing_session():
    service = ConversationService()

    session_id = "openai-response-update-1"

    service.save_openai_response_id(
        session_id=session_id,
        tenant_id=TENANT_LPDB.tenant_id,
        response_id="response_old_123",
    )

    service.save_openai_response_id(
        session_id=session_id,
        tenant_id=TENANT_LPDB.tenant_id,
        response_id="response_new_456",
    )

    recovered = service.get_openai_response_id(
        session_id=session_id,
        tenant_id=TENANT_LPDB.tenant_id,
    )

    assert recovered == "response_new_456"

    service._clear_state(
        session_id=session_id,
        tenant_id=TENANT_LPDB.tenant_id,
    )


def test_missing_openai_response_id_returns_none():
    service = ConversationService()

    result = service.get_openai_response_id(
        session_id="openai-response-does-not-exist",
        tenant_id=TENANT_LPDB.tenant_id,
    )

    assert result is None

def test_save_state_preserves_existing_openai_response_id():
    service = ConversationService()

    session_id = "conversation-state-openai-preservation-1"

    service.save_openai_response_id(
        session_id=session_id,
        tenant_id=TENANT_LPDB.tenant_id,
        response_id="response_preserve_123",
    )

    state = ConversationState(
        status="waiting_combo_confirmation",
        customer_name="Carolina",
        location_id=1,
        combo_product="PERRO DEL BARRIO",
    )

    service._save_state(
        session_id=session_id,
        state=state,
        tenant_id=TENANT_LPDB.tenant_id,
    )

    recovered_response_id = (
        service.get_openai_response_id(
            session_id=session_id,
            tenant_id=TENANT_LPDB.tenant_id,
        )
    )

    recovered_state = service.get_state(
        session_id=session_id,
        tenant_id=TENANT_LPDB.tenant_id,
    )

    assert recovered_response_id == (
        "response_preserve_123"
    )

    assert recovered_state.status == (
        "waiting_combo_confirmation"
    )

    assert recovered_state.customer_name == (
        "Carolina"
    )

    assert recovered_state.location_id == 1

    assert recovered_state.combo_product == (
        "PERRO DEL BARRIO"
    )

    service._clear_state(
        session_id=session_id,
        tenant_id=TENANT_LPDB.tenant_id,
    )