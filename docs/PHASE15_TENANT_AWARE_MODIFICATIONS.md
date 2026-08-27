# Phase 15 — Tenant-aware modifications

El servicio de modificaciones debe recibir el `tenant_id` o un `TenantContext` confiable y nunca resolver productos mediante un identificador global únicamente.

Reglas obligatorias:

- La receta debe resolverse dentro del tenant.
- La categoría del producto debe resolverse dentro del tenant.
- Un cambio de base debe buscar el producto equivalente dentro del tenant.
- El LLM no suministra el tenant; la aplicación lo resuelve antes de llamar la tool.
- Los precios de adiciones siguen siendo reglas de negocio internas y no sustituyen el cobro final de Toast.

## Próximo cambio

Adaptar `modification_service.py` de forma incremental, validando primero las consultas de producto/receta antes de actualizar `agent_tools.py` para modificaciones.
