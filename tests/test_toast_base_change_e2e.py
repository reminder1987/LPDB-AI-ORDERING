from decimal import Decimal

from app.models.order_db import OrderDB
from app.models.order_item_db import (
    OrderItemDB,
)
from app.models.order_item_modification_db import (
    OrderItemModificationDB,
)
from app.services.external_mapping_service import (
    create_external_mapping,
)
from app.services.external_order_mapper import (
    build_external_order_payload,
)
from app.services.toast_order_adapter import (
    ToastOrderAdapter,
)


def test_base_change_reaches_final_toast_product():
    """
    Valida el flujo completo de identidad de producto
    para un BASE_CHANGE:

    OrderDB
        -> OrderItemDB
        -> OrderItemModificationDB
        -> external order payload
        -> ToastOrderAdapter
        -> Toast target product GUID

    El producto original NO debe llegar a Toast cuando
    existe un BASE_CHANGE válido hacia otro producto.
    """

    tenant_id = 1

    original_product_id = 80
    target_product_id = 81

    original_product_guid = (
        "toast-product-arepa-pollo"
    )

    target_product_guid = (
        "toast-product-patacon-pollo"
    )

    target_group_guid = (
        "toast-group-patacones"
    )

    # ====================================================
    # 1. CONSTRUIR ORDEN INTERNA
    # ====================================================

    order = OrderDB(
        id=900,
        tenant_id=tenant_id,
        customer_name=(
            "Cliente Base Change E2E"
        ),
        location_id=1,
        total=Decimal("12.99"),
    )

    order_item = OrderItemDB(
        id=901,
        order_id=900,
        product_id=original_product_id,
        quantity=1,
        unit_price=Decimal("12.99"),
        subtotal=Decimal("12.99"),
    )

    base_change = (
        OrderItemModificationDB(
            id=902,
            order_item_id=901,
            modification_type=(
                "BASE_CHANGE"
            ),
            ingredient_id=None,
            ingredient_name=None,
            new_base="PATACON",
            new_product_id=(
                target_product_id
            ),
            new_product_name=(
                "PATACÓN DE POLLO"
            ),
            price=Decimal("0.00"),
        )
    )

    order_item.modifications = [
        base_change
    ]

    order.items = [
        order_item
    ]

    # ====================================================
    # 2. CONVERTIR A PAYLOAD EXTERNO NEUTRAL
    # ====================================================

    external_payload = (
        build_external_order_payload(
            order
        )
    )

    assert (
        external_payload["order_id"]
        == 900
    )

    assert (
        external_payload["tenant_id"]
        == tenant_id
    )

    assert len(
        external_payload["items"]
    ) == 1

    external_item = (
        external_payload["items"][0]
    )

    assert (
        external_item["product_id"]
        == original_product_id
    )

    assert len(
        external_item["modifications"]
    ) == 1

    external_base_change = (
        external_item[
            "modifications"
        ][0]
    )

    assert (
        external_base_change["type"]
        == "BASE_CHANGE"
    )

    assert (
        external_base_change[
            "new_product_id"
        ]
        == target_product_id
    )

    assert (
        external_base_change[
            "new_product_name"
        ]
        == "PATACÓN DE POLLO"
    )

    assert (
        external_base_change[
            "new_base"
        ]
        == "PATACON"
    )

    # ====================================================
    # 3. CREAR MAPPINGS TOAST
    # ====================================================

    create_external_mapping(
        tenant_id=tenant_id,
        provider="toast",
        entity_type="product",
        internal_id=(
            original_product_id
        ),
        external_id=(
            original_product_guid
        ),
    )

    create_external_mapping(
        tenant_id=tenant_id,
        provider="toast",
        entity_type=(
            "product_group"
        ),
        internal_id=(
            original_product_id
        ),
        external_id=(
            "toast-group-arepas"
        ),
    )

    create_external_mapping(
        tenant_id=tenant_id,
        provider="toast",
        entity_type="product",
        internal_id=(
            target_product_id
        ),
        external_id=(
            target_product_guid
        ),
    )

    create_external_mapping(
        tenant_id=tenant_id,
        provider="toast",
        entity_type=(
            "product_group"
        ),
        internal_id=(
            target_product_id
        ),
        external_id=(
            target_group_guid
        ),
    )

    # ====================================================
    # 4. CONSTRUIR PAYLOAD FINAL TOAST
    # ====================================================

    adapter = ToastOrderAdapter(
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
        dining_option_guid=(
            "toast-dining-option-001"
        ),
        tenant_id=tenant_id,
    )

    toast_payload = (
        adapter.build_order_payload(
            external_payload
        )
    )

    # ====================================================
    # 5. VALIDAR PAYLOAD FINAL
    # ====================================================

    assert toast_payload[
        "externalId"
    ] == (
        "lpdb-order-1-900"
    )

    assert toast_payload[
        "diningOption"
    ] == {
        "guid": (
            "toast-dining-option-001"
        ),
    }

    assert len(
        toast_payload["checks"]
    ) == 1

    check = (
        toast_payload["checks"][0]
    )

    assert check[
        "externalId"
    ] == (
        "lpdb-check-1-900"
    )

    assert len(
        check["selections"]
    ) == 1

    selection = (
        check["selections"][0]
    )

    assert selection[
        "externalId"
    ] == (
        "lpdb-selection-1-901"
    )

    # ====================================================
    # 6. BASE_CHANGE DEBE CAMBIAR PRODUCTO REAL EN TOAST
    # ====================================================

    assert selection["item"] == {
        "guid": target_product_guid,
    }

    assert selection[
        "itemGroup"
    ] == {
        "guid": target_group_guid,
    }

    assert (
        selection["item"]["guid"]
        != original_product_guid
    )

    assert (
        selection["itemGroup"]["guid"]
        != "toast-group-arepas"
    )

    # BASE_CHANGE no debe convertirse en modifier Toast.
    # Su efecto es sustituir el producto efectivo.

    assert (
        selection["modifiers"]
        == []
    )

    assert (
        selection["quantity"]
        == 1
    )