from fastapi import FastAPI

from app.api.orders import router as orders_router
from app.core.config import settings


app = FastAPI(title=settings.app_name)

app.include_router(orders_router)


@app.get("/")
def home():
    return {
        "status": "ok",
        "message": f"{settings.app_name} está funcionando",
        "environment": settings.environment,
    }