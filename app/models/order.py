from pydantic import BaseModel


class Order(BaseModel):
    customer_name: str
    product: str
    quantity: int