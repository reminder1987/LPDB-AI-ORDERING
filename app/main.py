from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agent import router as agent_router
from app.api.auth import router as auth_router
from app.api.availability import router as availability_router
from app.api.channels import router as channels_router
from app.api.health import router as health_router
from app.api.orders import router as orders_router
from app.api.operational import router as operational_router
from app.api.products import router as products_router
from app.api.webhooks import router as webhooks_router

from app.core.config import settings
from app.core.logging import configure_logging
from app.core.observability_middleware import (
    ObservabilityMiddleware,
)
from app.core.operational_monitor import operational_monitor
from app.core.operational_monitor_worker import (
    OperationalMonitorWorker,
)


configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    worker: OperationalMonitorWorker | None = None
    task: asyncio.Task[None] | None = None

    if settings.operational_monitor_enabled:
        worker = OperationalMonitorWorker(
            poll=operational_monitor.poll,
            interval_seconds=(
                settings.operational_monitor_interval_seconds
            ),
        )

        task = asyncio.create_task(
            worker.run(),
            name="operational-monitor",
        )

    try:
        yield
    finally:
        if worker is not None:
            worker.stop()

        if task is not None:
            with suppress(asyncio.CancelledError):
                await task


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    ObservabilityMiddleware,
)


app.include_router(agent_router)
app.include_router(auth_router)
app.include_router(availability_router)
app.include_router(channels_router)
app.include_router(health_router)
app.include_router(orders_router)
app.include_router(operational_router)
app.include_router(products_router)
app.include_router(webhooks_router)


@app.get("/")
def home():
    return {
        "status": "ok",
        "message": (
            f"{settings.app_name} esta funcionando"
        ),
        "environment": settings.environment,
    }
