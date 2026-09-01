from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class OrderModificationCreate(BaseModel):
    type: Literal[
        "REMOVE",
        "ADD",
        "BASE_CHANGE",
    ]

    ingredient: str | None = Field(
        default=None,
        min_length=1,
    )

    new_base: str | None = Field(
        default=None,
        min_length=1,
    )


class OrderItemCreate(BaseModel):
    product: str = Field(
        min_length=1,
    )

    quantity: int = Field(
        gt=0,
    )

    modifications: list[OrderModificationCreate] = Field(
        default_factory=list,
    )

    combo_requested: bool = Field(
        default=False,
    )

    beverage_product_id: int | None = Field(
        default=None,
    )

    beverage_product: str | None = Field(
        default=None,
        min_length=1,
    )


class OrderCreate(BaseModel):
    customer_name: str = Field(
        min_length=1,
    )

    # ---------------------------------------------------------
    # Cliente
    #
    # Permite vincular la orden con el CustomerDB.
    #
    # Es opcional para mantener compatibilidad con consumidores
    # legacy que todavía crean órdenes sin identidad de cliente.
    # ---------------------------------------------------------

    customer_id: int | None = Field(
        default=None,
        gt=0,
    )

    # La sede es obligatoria para cualquier pedido nuevo.
    location_id: int = Field(
        gt=0,
    )

    # Nueva estructura: una orden puede tener múltiples productos.
    items: list[OrderItemCreate] = Field(
        default_factory=list,
    )

    # Campos legacy para no romper consumidores existentes.
    product: str | None = Field(
        default=None,
        min_length=1,
    )

    quantity: int | None = Field(
        default=None,
        gt=0,
    )

    modifications: list[OrderModificationCreate] = Field(
        default_factory=list,
    )

    combo_requested: bool = Field(
        default=False,
    )

    beverage_product_id: int | None = Field(
        default=None,
    )

    beverage_product: str | None = Field(
        default=None,
        min_length=1,
    )


class OrderModificationResponse(BaseModel):
    type: str
    ingredient: str | None = None
    new_base: str | None = None
    price: Decimal | None = None


class OrderBeverageResponse(BaseModel):
    product_id: int
    product: str


class OrderComboResponse(BaseModel):
    requested: bool
    fries: str
    beverage: OrderBeverageResponse | None = None

    # Precio adicional del combo.
    #
    # Actualmente:
    # $6.99
    #
    # Las papas y la bebida están incluidas.
    price: Decimal | None = None


class OrderItemResponse(BaseModel):
    product: str
    quantity: int

    modifications: list[
        OrderModificationResponse
    ] = Field(
        default_factory=list,
    )

    combo: OrderComboResponse | None = None

    # Precio del producto final antes de multiplicar
    # por la cantidad.
    unit_price: Decimal | None = None

    # Precio total de este item:
    #
    # unit_price × quantity
    subtotal: Decimal | None = None


class OrderResponse(BaseModel):
    id: int
    status: str
    customer_name: str

    # Puede ser NULL únicamente en pedidos legacy creados
    # antes de que la sede fuera obligatoria en el modelo.
    #
    # Los pedidos nuevos continúan exigiendo location_id
    # mediante OrderCreate.
    location_id: int | None = None

    # ---------------------------------------------------------
    # Campos legacy
    #
    # Se mantienen para no romper consumidores existentes.
    # ---------------------------------------------------------

    product: str
    quantity: int

    modifications: list[
        OrderModificationResponse
    ] = Field(
        default_factory=list,
    )

    combo: OrderComboResponse | None = None

    # ---------------------------------------------------------
    # Nueva representación completa.
    # ---------------------------------------------------------

    items: list[OrderItemResponse] = Field(
        default_factory=list,
    )

    # Suma de los subtotales de todos los items.
    subtotal: Decimal | None = None

    # Total final de la orden.
    #
    # Actualmente no existen impuestos,
    # descuentos ni cargos adicionales en
    # las reglas de negocio.
    total: Decimal | None = None


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