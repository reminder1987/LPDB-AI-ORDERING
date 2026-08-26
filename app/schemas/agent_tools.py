from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class SearchProductsInput(BaseModel):
    query: str = Field(min_length=1)


class GetProductRecipeInput(BaseModel):
    product_id: int = Field(gt=0)


class CheckProductAvailabilityInput(BaseModel):
    product_id: int = Field(gt=0)
    location_id: int = Field(gt=0)


class CheckIngredientAvailabilityInput(BaseModel):
    ingredient_id: int = Field(gt=0)
    location_id: int = Field(gt=0)


class ValidateModificationInput(BaseModel):
    product_id: int = Field(gt=0)
    type: Literal["REMOVE", "ADD", "BASE_CHANGE"]
    ingredient: str | None = Field(default=None, min_length=1)
    new_base: str | None = Field(default=None, min_length=1)


class GetLocationInput(BaseModel):
    query: str = Field(min_length=1)


class OrderItemPriceInput(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    modifications: list[ValidateModificationInput] = Field(default_factory=list)
    combo_requested: bool = False


class CalculateOrderPriceInput(BaseModel):
    items: list[OrderItemPriceInput] = Field(min_length=1)


class CreateOrderInput(BaseModel):
    customer_name: str = Field(min_length=1)
    location_id: int = Field(gt=0)
    items: list[OrderItemPriceInput] = Field(min_length=1)


class ToolError(BaseModel):
    ok: bool = False
    error: str


class PricePreview(BaseModel):
    ok: bool = True
    items: list[dict]
    subtotal: Decimal
    total: Decimal
    note: str = (
        "Cálculo interno de LPDB. El monto final de cobro será "
        "determinado por Toast cuando exista la integración."
    )
