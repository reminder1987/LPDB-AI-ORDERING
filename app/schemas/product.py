from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProductResponse(BaseModel):
    id: int
    name: str
    category_id: int
    price: Decimal

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    status: str
    products: list[ProductResponse]


class ProductSearchResponse(BaseModel):
    status: str
    products: list[ProductResponse]