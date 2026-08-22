from app.data.orders import orders
from app.models.order import Order


def create_order(order: Order):
    order_data = order.model_dump()
    orders.append(order_data)
    return order_data


def get_orders():
    return orders