from fastapi import APIRouter, HTTPException, Response

from app.models.order import Order
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


@router.get("/test")
def test_orders():
    return {
        "status": "ok",
        "message": "Orders API está funcionando",
    }


@router.post("/", status_code=201)
def create_order_endpoint(order: Order):
    saved_order = create_order(order)

    return {
        "status": "ok",
        "message": "Pedido recibido correctamente",
        "order": saved_order,
    }


@router.get("/")
def get_orders_endpoint():
    return {
        "status": "ok",
        "orders": get_orders(),
    }


@router.get("/{order_id}")
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


@router.put("/{order_id}")
def update_order_endpoint(order_id: int, order: Order):
    updated_order = update_order(order_id, order)

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


@router.delete("/{order_id}", status_code=204)
def delete_order_endpoint(order_id: int):
    deleted = delete_order(order_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado",
        )

    return Response(status_code=204)