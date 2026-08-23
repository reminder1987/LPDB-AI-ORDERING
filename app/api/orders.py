from fastapi import APIRouter
from app.models.order import Order
from app.services.order_service import create_order, get_orders, get_order_by_id


router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


@router.get("/test")
def test_orders():
    return {
        "status": "ok",
        "message": "Orders API está funcionando"
    }


@router.post("/")
def create_order_endpoint(order: Order):
    saved_order = create_order(order)

    return {
        "status": "ok",
        "message": "Pedido recibido correctamente",
        "order": saved_order
    }


@router.get("/")
def get_orders_endpoint():
    return {
        "status": "ok",
        "orders": get_orders()
    }

@router.get("/{order_id}")
def get_order_endpoint(order_id: int):
    order = get_order_by_id(order_id)

    if order is None:
        return {
            "status": "error",
            "message": "Pedido no encontrado"
        }

    return {
        "status": "ok",
        "order": order
    }
