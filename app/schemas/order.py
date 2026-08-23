from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    customer_name: str = Field(
        min_length=1,
        description="Nombre del cliente que realiza el pedido.",
        examples=["Carolina"],
    )

    product: str = Field(
        min_length=1,
        description="Producto solicitado.",
        examples=["Pizza"],
    )

    quantity: int = Field(
        gt=0,
        description="Cantidad de unidades solicitadas. Debe ser mayor que 0.",
        examples=[2],
    )


class OrderResponse(BaseModel):
    id: int = Field(
        description="Identificador único del pedido.",
        examples=[1],
    )

    customer_name: str = Field(
        description="Nombre del cliente.",
        examples=["Carolina"],
    )

    product: str = Field(
        description="Producto solicitado.",
        examples=["Pizza"],
    )

    quantity: int = Field(
        description="Cantidad de unidades solicitadas.",
        examples=[2],
    )


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