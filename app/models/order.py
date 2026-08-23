from pydantic import BaseModel, Field


class Order(BaseModel):
    customer_name: str = Field(min_length=1)
    product: str = Field(min_length=1)
    quantity: int = Field(gt=0)