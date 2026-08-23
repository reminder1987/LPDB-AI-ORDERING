from app.core.database import SessionLocal
from app.schemas.order import OrderCreate
from app.models.order_db import OrderDB


def create_order(order: OrderCreate):
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


def get_order_by_id(order_id: int):
    db = SessionLocal()

    try:
        order = (
            db.query(OrderDB)
            .filter(OrderDB.id == order_id)
            .first()
        )

        if order is None:
            return None

        return {
            "id": order.id,
            "customer_name": order.customer_name,
            "product": order.product,
            "quantity": order.quantity,
        }

    finally:
        db.close()


def delete_order(order_id: int):
    db = SessionLocal()

    try:
        order = (
            db.query(OrderDB)
            .filter(OrderDB.id == order_id)
            .first()
        )

        if order is None:
            return False

        db.delete(order)
        db.commit()

        return True

    finally:
        db.close()


def update_order(order_id: int, order: OrderCreate):
    db = SessionLocal()

    try:
        order_db = (
            db.query(OrderDB)
            .filter(OrderDB.id == order_id)
            .first()
        )

        if order_db is None:
            return None

        order_db.customer_name = order.customer_name
        order_db.product = order.product
        order_db.quantity = order.quantity

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