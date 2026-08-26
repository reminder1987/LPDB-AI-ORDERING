from fastapi import FastAPI

from app.api.agent import router as agent_router
from app.api.availability import router as availability_router
from app.api.orders import router as orders_router
from app.api.products import router as products_router

from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
)

app.include_router(agent_router)
app.include_router(availability_router)
app.include_router(orders_router)
app.include_router(products_router)


@app.get("/")
def home():
    return {
        "status": "ok",
        "message": f"{settings.app_name} está funcionando",
        "environment": settings.environment,
    }