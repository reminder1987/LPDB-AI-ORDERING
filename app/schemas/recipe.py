from pydantic import BaseModel, ConfigDict


class RecipeIngredientResponse(BaseModel):
    id: int
    name: str
    category: str

    model_config = ConfigDict(from_attributes=True)


class RecipeResponse(BaseModel):
    product_id: int
    product_name: str
    ingredients: list[RecipeIngredientResponse]


class ModificationValidationResponse(BaseModel):
    allowed: bool
    reason: str
    ingredient: str | None = None
    new_base: str | None = None
    price: int | float | None = None