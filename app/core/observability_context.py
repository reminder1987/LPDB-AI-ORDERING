from __future__ import annotations

import contextvars
from dataclasses import dataclass
from typing import Any


_request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id",
    default=None,
)

_tenant_id: contextvars.ContextVar[int | None] = contextvars.ContextVar(
    "tenant_id",
    default=None,
)

_tenant_slug: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "tenant_slug",
    default=None,
)


@dataclass(frozen=True)
class ObservabilityContext:
    request_id: str | None
    tenant_id: int | None
    tenant_slug: str | None


def set_request_id(request_id: str | None) -> contextvars.Token:
    return _request_id.set(request_id)


def reset_request_id(token: contextvars.Token) -> None:
    _request_id.reset(token)


def get_request_id() -> str | None:
    return _request_id.get()


def set_tenant_id(tenant_id: int | None) -> contextvars.Token:
    return _tenant_id.set(tenant_id)


def reset_tenant_id(token: contextvars.Token) -> None:
    _tenant_id.reset(token)


def get_tenant_id() -> int | None:
    return _tenant_id.get()


def set_tenant_slug(tenant_slug: str | None) -> contextvars.Token:
    return _tenant_slug.set(tenant_slug)


def reset_tenant_slug(token: contextvars.Token) -> None:
    _tenant_slug.reset(token)


def get_tenant_slug() -> str | None:
    return _tenant_slug.get()


def get_observability_context() -> ObservabilityContext:
    return ObservabilityContext(
        request_id=get_request_id(),
        tenant_id=get_tenant_id(),
        tenant_slug=get_tenant_slug(),
    )


def context_fields() -> dict[str, Any]:
    context = get_observability_context()

    fields: dict[str, Any] = {}

    if context.request_id is not None:
        fields["request_id"] = context.request_id

    if context.tenant_id is not None:
        fields["tenant_id"] = context.tenant_id

    if context.tenant_slug is not None:
        fields["tenant_slug"] = context.tenant_slug

    return fields
