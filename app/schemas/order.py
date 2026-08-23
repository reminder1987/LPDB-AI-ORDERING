from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=1)
    product: str = Field(min_length=1)
    quantity: int = Field(gt=0)


class OrderResponse(BaseModel):
    id: int
    customer_name: str
    product: str
    quantity: int


class OrderCreateResponse(BaseModel):
    status: str
    message: str
    order: OrderResponse


class OrderResponseWrapper(BaseModel):
    status: str
    order: OrderResponse


class OrderListResponse(BaseModel):
    status: str
    orders: list[OrderResponse]


class MessageResponse(BaseModel):
    status: str
    message: str
    