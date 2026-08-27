from app.services.modification_service import (
    validate_addition,
    validate_base_change,
    validate_removal,
)


TENANT_LPDB = 1
INVALID_TENANT = 999999
PRODUCT_PERRO_DEL_BARRIO = 2


def test_validate_removal_respects_tenant():
    result = validate_removal(
        PRODUCT_PERRO_DEL_BARRIO,
        "TOCINETA",
        TENANT_LPDB,
    )
    assert result["allowed"] is True
    assert result["ingredient"] == "TOCINETA"

    isolated = validate_removal(
        PRODUCT_PERRO_DEL_BARRIO,
        "TOCINETA",
        INVALID_TENANT,
    )
    assert isolated == {
        "allowed": False,
        "reason": "Producto no encontrado",
    }


def test_validate_addition_respects_tenant():
    result = validate_addition(
        PRODUCT_PERRO_DEL_BARRIO,
        "TOCINETA",
        TENANT_LPDB,
    )
    assert result["allowed"] is True
    assert str(result["price"]) == "4.00"

    isolated = validate_addition(
        PRODUCT_PERRO_DEL_BARRIO,
        "TOCINETA",
        INVALID_TENANT,
    )
    assert isolated == {
        "allowed": False,
        "reason": "Producto no encontrado",
    }


def test_validate_base_change_respects_tenant():
    result = validate_base_change(
        PRODUCT_PERRO_DEL_BARRIO,
        "PATACON",
        TENANT_LPDB,
    )
    assert result["allowed"] is False
    assert result["reason"] == "La base de este producto no se puede cambiar"

    isolated = validate_base_change(
        PRODUCT_PERRO_DEL_BARRIO,
        "PATACON",
        INVALID_TENANT,
    )
    assert isolated == {
        "allowed": False,
        "reason": "Producto no encontrado",
    }
