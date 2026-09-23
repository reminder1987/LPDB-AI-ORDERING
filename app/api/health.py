from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.services.health_service import check_database


router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get("/live")
def liveness():
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
    }


@router.get("/ready")
def readiness():
    database = check_database()

    if not database.healthy:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "checks": {
                    "database": "unavailable",
                },
            },
        )

    return {
        "status": "ready",
        "checks": {
            "database": "ok",
        },
    }


@router.get("")
def health():
    database = check_database()

    if not database.healthy:
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "checks": {
                    "api": "ok",
                    "database": "unavailable",
                },
            },
        )

    return {
        "status": "ok",
        "checks": {
            "api": "ok",
            "database": "ok",
        },
    }
