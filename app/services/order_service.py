from app.core.database import SessionLocal
from app.models.order import Order
from app.models.order_db import OrderDB


def create_order(order: Order):
    db = SessionLocal()

    try:
        order_db = OrderDB(
            customer_name=order.customer_name,
            product=order.product,
            quantity=order.quantity,
        )

        db.add(order_db)
        db.commit()
        db.refresh(order_db)

        return {
            "id": order_db.id,
            "customer_name": order_db.customer_name,
            "product": order_db.product,
            "quantity": order_db.quantity,
        }

    finally:
        db.close()


def get_orders():
    db = SessionLocal()

    try:
        orders = db.query(OrderDB).all()

        return [
            {
                "id": order.id,
                "customer_name": order.customer_name,
                "product": order.product,
                "quantity": order.quantity,
            }
            for order in orders
        ]

    finally:
        db.close()