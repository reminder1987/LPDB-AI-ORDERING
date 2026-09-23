from __future__ import annotations

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.logging import get_logger
from app.core.observability_context import (
    reset_request_id,
    reset_tenant_slug,
    set_request_id,
    set_tenant_slug,
)


logger = get_logger("lpdb.http")

MAX_REQUEST_ID_LENGTH = 128
MAX_TENANT_SLUG_LENGTH = 128


def normalize_request_id(value: str | None) -> str:
    candidate = (value or "").strip()

    if (
        candidate
        and len(candidate) <= MAX_REQUEST_ID_LENGTH
        and candidate.isprintable()
    ):
        return candidate

    return str(uuid.uuid4())


def normalize_tenant_slug(value: str | None) -> str | None:
    candidate = (value or "").strip()

    if not candidate:
        return None

    if len(candidate) > MAX_TENANT_SLUG_LENGTH:
        return None

    if not candidate.isprintable():
        return None

    return candidate


def classify_http_status(status_code: int) -> str:
    if status_code >= 500:
        return "server_error"

    if status_code >= 400:
        return "client_error"

    if status_code >= 300:
        return "redirect"

    return "success"


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        request_id = normalize_request_id(
            request.headers.get("X-Request-ID")
        )

        tenant_slug = normalize_tenant_slug(
            request.headers.get("X-Tenant")
        )

        request_token = set_request_id(request_id)
        tenant_slug_token = set_tenant_slug(tenant_slug)

        started_at = time.perf_counter()

        logger.info(
            "http_request_started",
            extra={
                "event": "http_request_started",
                "http_method": request.method,
                "http_path": request.url.path,
            },
        )

        try:
            response = await call_next(request)

            duration_ms = round(
                (time.perf_counter() - started_at) * 1000,
                2,
            )

            response.headers["X-Request-ID"] = request_id

            logger.info(
                "http_request_completed",
                extra={
                    "event": "http_request_completed",
                    "http_method": request.method,
                    "http_path": request.url.path,
                    "http_status": response.status_code,
                    "outcome": classify_http_status(
                        response.status_code
                    ),
                    "duration_ms": duration_ms,
                },
            )

            return response

        except Exception:
            duration_ms = round(
                (time.perf_counter() - started_at) * 1000,
                2,
            )

            logger.exception(
                "http_request_failed",
                extra={
                    "event": "http_request_failed",
                    "http_method": request.method,
                    "http_path": request.url.path,
                    "outcome": "unhandled_exception",
                    "duration_ms": duration_ms,
                },
            )

            raise

        finally:
            reset_tenant_slug(tenant_slug_token)
            reset_request_id(request_token)
