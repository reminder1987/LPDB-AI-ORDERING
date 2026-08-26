from fastapi import APIRouter, HTTPException, Response

from app.schemas.order import (
    OrderCreate,
    OrderCreateResponse,
    OrderListResponse,
    OrderResponseWrapper,
)
from app.services.order_service import (
    create_order,
    get_orders,
    get_order_by_id,
    update_order,
    delete_order,
)


router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


@router.get(
    "/test",
    summary="Verificar estado de la API de pedidos",
    description=(
        "Comprueba que el módulo de pedidos está funcionando "
        "correctamente."
    ),
)
def test_orders():
    return {
        "status": "ok",
        "message": "Orders API está funcionando",
    }


@router.post(
    "/",
    status_code=201,
    response_model=OrderCreateResponse,
    summary="Crear un nuevo pedido",
    description=(
        "Crea un nuevo pedido y lo almacena en la base de datos. "
        "El pedido debe indicar la sede mediante location_id. "
        "Las modificaciones y el combo solicitado se validan "
        "contra las reglas del catálogo antes de guardar."
    ),
    responses={
        400: {
            "description": (
                "El pedido, la sede o alguna de sus modificaciones "
                "no está permitido."
            ),
        },
    },
)
def create_order_endpoint(order: OrderCreate):
    try:
        saved_order = create_order(order)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "status": "ok",
        "message": "Pedido recibido correctamente",
        "order": saved_order,
    }


@router.get(
    "/",
    response_model=OrderListResponse,
    summary="Obtener todos los pedidos",
    description=(
        "Devuelve la lista completa de pedidos almacenados, "
        "incluyendo la sede asociada cuando está disponible."
    ),
)
def get_orders_endpoint():
    return {
        "status": "ok",
        "orders": get_orders(),
    }


@router.get(
    "/{order_id}",
    response_model=OrderResponseWrapper,
    summary="Obtener un pedido por ID",
    description=(
        "Busca y devuelve un pedido utilizando su identificador único, "
        "incluyendo la sede asociada."
    ),
    responses={
        404: {
            "description": "El pedido solicitado no existe.",
        },
    },
)
def get_order_endpoint(order_id: int):
    order = get_order_by_id(order_id)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado",
        )

    return {
        "status": "ok",
        "order": order,
    }


@router.put(
    "/{order_id}",
    response_model=OrderResponseWrapper,
    summary="Actualizar un pedido",
    description=(
        "Actualiza los datos de un pedido existente utilizando su "
        "identificador único. La sede también puede actualizarse "
        "mediante location_id."
    ),
    responses={
        400: {
            "description": (
                "El pedido, la sede o alguna de sus modificaciones "
                "no está permitido."
            ),
        },
        404: {
            "description": (
                "El pedido que se desea actualizar no existe."
            ),
        },
    },
)
def update_order_endpoint(
    order_id: int,
    order: OrderCreate,
):
    try:
        updated_order = update_order(
            order_id,
            order,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if updated_order is None:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado",
        )

    return {
        "status": "ok",
        "message": "Pedido actualizado correctamente",
        "order": updated_order,
    }


@router.delete(
    "/{order_id}",
    status_code=204,
    response_model=None,
    summary="Eliminar un pedido",
    description=(
        "Elimina definitivamente un pedido existente utilizando "
        "su identificador único."
    ),
    responses={
        404: {
            "description": "El pedido que se desea eliminar no existe.",
        },
    },
)
def delete_order_endpoint(order_id: int):
    deleted = delete_order(order_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado",
        )

    return Response(status_code=204)