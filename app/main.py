from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.activity import router as activity_router
from app.api.admin_locations import router as admin_locations_router
from app.api.admin_users import router as admin_users_router
from app.api.agent import router as agent_router
from app.api.auth import router as auth_router
from app.api.availability import router as availability_router
from app.api.business_metrics import router as business_metrics_router
from app.api.business_settings import router as business_settings_router
from app.api.channels import router as channels_router
from app.api.configuration import router as configuration_router
from app.api.customers import router as customers_router
from app.api.health import router as health_router
from app.api.integrations import router as integrations_router
from app.api.orders import router as orders_router
from app.api.operational import router as operational_router
from app.api.payments import router as payments_router
from app.api.products import router as products_router
from app.api.webhooks import router as webhooks_router

from app.core.config import settings
from app.core.logging import configure_logging
from app.core.meta_whatsapp_delivery_worker import (
    MetaWhatsAppDeliveryWorker,
)
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
    operational_worker: OperationalMonitorWorker | None = None
    operational_task: asyncio.Task[None] | None = None

    meta_worker: MetaWhatsAppDeliveryWorker | None = None
    meta_task: asyncio.Task[None] | None = None

    if settings.operational_monitor_enabled:
        operational_worker = OperationalMonitorWorker(
            poll=operational_monitor.poll,
            interval_seconds=(
                settings.operational_monitor_interval_seconds
            ),
        )

        operational_task = asyncio.create_task(
            operational_worker.run(),
            name="operational-monitor",
        )

    if settings.meta_whatsapp_delivery_worker_enabled:
        meta_worker = MetaWhatsAppDeliveryWorker(
            interval_seconds=(
                settings.meta_whatsapp_delivery_worker_interval_seconds
            ),
            lease_seconds=(
                settings.meta_whatsapp_delivery_worker_lease_seconds
            ),
            batch_size=(
                settings.meta_whatsapp_delivery_worker_batch_size
            ),
        )

        meta_task = asyncio.create_task(
            meta_worker.run(),
            name="meta-whatsapp-delivery",
        )

    try:
        yield
    finally:
        if operational_worker is not None:
            operational_worker.stop()

        if meta_worker is not None:
            meta_worker.stop()

        if operational_task is not None:
            with suppress(asyncio.CancelledError):
                await operational_task

        if meta_task is not None:
            with suppress(asyncio.CancelledError):
                await meta_task


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    ObservabilityMiddleware,
)


app.include_router(activity_router)
app.include_router(admin_locations_router)
app.include_router(admin_users_router)
app.include_router(agent_router)
app.include_router(auth_router)
app.include_router(availability_router)
app.include_router(business_metrics_router)
app.include_router(business_settings_router)
app.include_router(channels_router)
app.include_router(configuration_router)
app.include_router(customers_router)
app.include_router(health_router)
app.include_router(integrations_router)
app.include_router(orders_router)
app.include_router(operational_router)
app.include_router(payments_router)
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
