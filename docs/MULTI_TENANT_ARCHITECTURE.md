# Arquitectura multi-tenant — Diseño base

## Objetivo

Convertir LPDB-AI-ORDERING en una plataforma replicable para múltiples marcas de restaurantes, manteniendo a Los Perritos Del Barrio como el primer tenant.

## Principio

El código de plataforma es compartido. Los datos y configuraciones de cada marca deben quedar aislados mediante `tenant_id`.

```text
PLATFORM
  ├── Agent
  ├── Tools
  ├── Conversation
  ├── Ordering
  ├── Integrations
  └── Billing

TENANT
  ├── Catalog
  ├── Ingredients
  ├── Recipes
  ├── Locations
  ├── Availability
  ├── Conversations
  ├── Orders
  └── Toast configuration
```

## Entidades que deben pertenecer a un tenant

### Directamente por tenant

- `product_categories`
- `ingredient_categories`
- `products`
- `ingredients`
- `locations`
- `conversation_sessions`
- `orders`

### Heredadas por relación

- `location_hours` → pertenece al tenant a través de `locations`.
- `product_availability` → pertenece al tenant a través de `products` y `locations`.
- `ingredient_availability` → pertenece al tenant a través de `ingredients` y `locations`.
- `recipes` → pertenece al tenant a través de `products`.
- `recipe_ingredients` → pertenece al tenant a través de `recipes` e `ingredients`.
- `order_items` → pertenece al tenant a través de `orders`.
- `order_item_modifications` → pertenece al tenant a través de `order_items`.
- `order_item_combos` → pertenece al tenant a través de `order_items`.

## Reglas de unicidad

Las reglas actualmente globales deberán evolucionar a reglas por tenant donde corresponda.

Ejemplos:

```text
UNIQUE(tenant_id, product_name)
UNIQUE(tenant_id, ingredient_name)
UNIQUE(tenant_id, product_category_name)
UNIQUE(tenant_id, ingredient_category_name)
UNIQUE(tenant_id, location_customer_name)
```

Los identificadores de Toast seguirán siendo únicos en el alcance que corresponda al proveedor, pero no deben utilizarse como sustituto del aislamiento interno de tenants.

## Seguridad de consultas

Toda consulta de datos de negocio deberá tener un contexto de tenant resuelto antes de leer o modificar información.

No debe existir una consulta tipo:

```python
select(ProductDB)
```

en una ruta de negocio multi-tenant sin un filtro de tenant equivalente.

Objetivo:

```python
select(ProductDB).where(ProductDB.tenant_id == tenant_id)
```

## LPDB como Tenant #1

LPDB será cargado como un tenant real, no como una excepción permanente en el código.

La configuración inicial será conceptualmente:

```text
slug: lpdb
name: Los Perritos Del Barrio
active: true
```

## No duplicar código por cliente

No se crearán carpetas como:

```text
clients/lpdb/
clients/client_02/
clients/client_03/
```

para contener implementaciones distintas del mismo negocio.

Los clientes compartirán el mismo código de plataforma y se diferenciarán por datos/configuración.

## Integraciones

Las credenciales y configuración de proveedores externos (por ejemplo, Toast) deben estar asociadas al tenant y almacenarse fuera del repositorio.

Nunca se deben guardar claves secretas en archivos de configuración versionados.

## Estrategia de migración

No modificar todas las tablas de negocio en una sola migración destructiva.

Se recomienda:

1. Crear `tenants`.
2. Crear el tenant LPDB.
3. Añadir `tenant_id` nullable a las tablas directas con migración controlada.
4. Backfill de registros existentes hacia LPDB.
5. Verificar que no existan filas sin tenant.
6. Convertir `tenant_id` en `NOT NULL`.
7. Ajustar índices y restricciones de unicidad.
8. Modificar servicios para exigir contexto de tenant.
9. Añadir pruebas de aislamiento entre tenants.

## Estado actual

- `TenantDB`: creado.
- Migración de `tenants`: creada.
- Registro en `app.models`: realizado.
- Registro en Alembic metadata: realizado.
- `tenant_id` en tablas de negocio: pendiente.
- Aislamiento de consultas: pendiente.
- Backfill LPDB: pendiente.
- Pruebas multi-tenant: pendiente.
