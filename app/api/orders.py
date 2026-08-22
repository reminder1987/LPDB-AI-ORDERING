from fastapi import APIRouter
from app.models.order import Order
from app.services.order_service import create_order, get_orders


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