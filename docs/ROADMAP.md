# LPDB-AI-ORDERING — ROADMAP OFICIAL

## Fuente de verdad del proyecto

Este documento es la fuente oficial del orden, alcance y estado de las fases del proyecto.

### Reglas del roadmap

1. Las fases mantienen el orden establecido en este documento.

2. No se deben renumerar, eliminar, fusionar ni crear fases nuevas sin actualizar primero este documento.

3. Al cerrar una fase se debe actualizar su estado y registrar el checkpoint de Git correspondiente.

4. Cada fase debe tener objetivo, alcance, pruebas y criterio de cierre antes de marcarse como completada.

5. Si la conversación y este documento presentan una contradicción, primero se revisa el repositorio y se actualiza este documento de forma explícita antes de continuar.

6. El código de producción debe permanecer alineado con el roadmap y cada hito importante debe quedar versionado en GitHub.

---

# ESTADO ACTUAL

Fase actual: 19 — Integraciones externas

Estado: EN IMPLEMENTACIÓN AVANZADA — TOAST

Base funcional previa: ordering, conversación/agente, multi-tenant, canales y submission E2E ya implementados.

Hito transversal completado: Tenant Isolation

Último checkpoint funcional confirmado: 1a13959 — map combos and beverages into Toast payload

Rama de trabajo actual: feature/orderdb-tenant

Rama principal: master

---

# FASES DEL PROYECTO

## FASE 01 — Fundamentos del proyecto

**Estado:** COMPLETADA

## FASE 02 — API / CRUD inicial

**Estado:** COMPLETADA

## FASE 03 — PostgreSQL

**Estado:** COMPLETADA

## FASE 04 — Modelado de catálogo

**Estado:** COMPLETADA

## FASE 05 — Productos / recetas

**Estado:** COMPLETADA

## FASE 06 — Sedes / disponibilidad

**Estado:** COMPLETADA

## FASE 07 — Modificaciones

**Estado:** COMPLETADA

Reglas y persistencia de `ADD`, `REMOVE` y `BASE_CHANGE`.

## FASE 08 — Agent / Intent / conversación

**Estado:** COMPLETADA

Interpretación de mensajes, productos, cantidades, modificaciones, combos y flujo conversacional.

## FASE 09 — Integración completa de ordering

**Estado:** COMPLETADA

Integración de catálogo, modificaciones, disponibilidad, sedes, conversación y persistencia.

## FASE 10 — Precio final

**Estado:** COMPLETADA

- Precio base de productos.

- Precio de `ADD`.

- `REMOVE` sin costo adicional.

- `BASE_CHANGE` según producto/base resultante.

- Cantidades.

- Múltiples productos.

- Combos y bebida.

- Subtotal y total consistentes.

- No inventar precios de combo mientras no estén definidos.

## FASE 11 — Disponibilidad real

**Estado:** COMPLETADA

- Producto disponible/no disponible.

- Ingredientes y modificaciones según disponibilidad.

- Bebidas disponibles.

- Validación antes de crear la orden.

- Integración con el flujo conversacional.

## FASE 12 — Consulta de pedidos

**Estado:** COMPLETADA

### Alcance

- `GET /orders`

- `GET /orders/{id}`

- Respuesta completa con items, modificaciones, combo y precios.

- Manejo correcto de pedido inexistente.

- Pruebas contra PostgreSQL.

- Compatibilidad de respuesta con pedidos legacy que tienen `location_id = NULL`.

### Validaciones realizadas

- Consulta de los 79 pedidos existentes.

- Pedidos con `ADD`.

- Pedidos con `REMOVE`.

- Pedidos con `BASE_CHANGE`.

- Múltiples items.

- Combos y bebidas.

- Precio de combo.

- `unit_price`, `subtotal` y `total`.

- `404` para pedido inexistente.

### Checkpoint

`221116b` — `feat: completar consultas de pedidos fase 12`

---

# HITO TRANSVERSAL — TENANT ISOLATION

Estado: COMPLETADO

Este hito establece el aislamiento multi-tenant transversal del backend antes de avanzar hacia la capa de interacción del producto.

## Alcance implementado

Resolución del tenant mediante el header HTTP X-Tenant.

TenantContext como contexto de negocio.

Tenant obligatorio en los endpoints protegidos.

Validación de tenant inexistente o inactivo.

Propagación del tenant_id desde la capa HTTP hacia los servicios.

Aislamiento de productos por tenant.

Aislamiento de disponibilidad por tenant.

Aislamiento de sedes por tenant.

Aislamiento de órdenes y sesiones conversacionales por tenant.

Validaciones de disponibilidad conscientes de tenant.

Persistencia de tenant_id donde corresponde en el dominio de ordering.

## Validaciones realizadas

GET /products/ con X-Tenant: lpdb → correcto.

GET /products/ sin X-Tenant → rechazado.

GET /products/ con tenant inexistente → rechazado.

GET /availability/1/1 con X-Tenant: lpdb → correcto.

GET /availability/1/1 sin X-Tenant → rechazado.

Verificación de consistencia entre ingredientes y sedes.

Pruebas del flujo conversacional con tenant.

Compilación de los módulos API modificados.

git diff --check → limpio.

## Checkpoints Git

a9f290b — Add tenant context to conversation orders

333413d — Enforce tenant context on product and availability APIs

## Criterio de cierre

El backend cuenta con un contexto de tenant explícito y las APIs auditadas no pueden operar sin un tenant válido. El hito queda cerrado y respaldado en GitHub.

---

# FASE 13 — Canal de cliente, agente IA y dashboard operativo

**Estado:** BASE FUNCIONAL IMPLEMENTADA

## Objetivo

Construir la capa de interacción del producto alrededor de la visión real del negocio:

> El cliente no necesita descargar una aplicación nueva. El canal principal del cliente será WhatsApp, donde conversa con el agente de IA. El agente entiende y valida el pedido, confirma la orden y conduce el flujo hasta el pago mediante Toast. Una vez confirmado el pago, el pedido queda listo para el flujo operativo de Toast y su envío a cocina/KDS según la configuración del restaurante.

La interfaz web no será el frontend principal del cliente. El frontend web de esta fase será principalmente un **dashboard operativo para el restaurante/administrador**.

## Arquitectura conceptual

```text

                    CLIENTE

                       │

                       │ WhatsApp

                       ▼

              ┌─────────────────┐

              │  AGENTE DE IA   │

              │    WHATSAPP     │

              └────────┬────────┘

                       │

                       ▼

              CATÁLOGO / PRECIOS

              DISPONIBILIDAD

              MODIFICACIONES

                       │

                       ▼

                 CONFIRMA ORDEN

                       │

                       ▼

                 INTEGRACIÓN TOAST

                       │

                       ▼

                  PAGO EN TOAST

                       │

                       ▼

                ORDEN PAGADA

                       │

                       ▼

                 TOAST / KDS

                       │

                       ▼

                    COCINA

```

En paralelo:

```text

RESTAURANTE

     │

     ▼

DASHBOARD WEB

     │

     ├── Pedidos

     ├── Productos

     ├── Precios

     ├── Disponibilidad

     ├── Sedes

     └── Configuración

```

## 13.1 Canal WhatsApp

Definir e implementar el canal mediante el cual los clientes conversarán con el agente sin instalar una aplicación nueva.

Debe contemplar:

- Recepción de mensajes.

- Envío de respuestas.

- Identificación de cliente/conversación.

- Persistencia de sesión.

- Manejo de errores del canal.

- Confirmación conversacional del pedido.

El proveedor concreto de WhatsApp queda pendiente de decisión técnica antes de implementar la integración.

## 13.2 Agente de IA / conversación

Reutilizar el motor existente de `/agent/message` y `conversation_service` como núcleo de interpretación y conversación.

El canal externo no debe duplicar la lógica de intent, modificaciones, disponibilidad ni precios.

## 13.3 Confirmación del pedido

El cliente debe recibir una representación clara del pedido antes del pago, incluyendo cuando corresponda:

- Productos.

- Cantidades.

- Modificaciones.

- Combos.

- Bebidas.

- Subtotal.

- Total.

## 13.4 Toast como sistema de pago y POS

**No se construirá una pasarela de pagos propia para el producto.**

La arquitectura objetivo es integrar Toast para que el pedido pueda entrar en su ecosistema de POS/pagos. Toast será la referencia externa para el precio final y el flujo de pago, sujeto a los permisos, capacidades y configuración del restaurante y de la integración aprobada por Toast.

Flujo objetivo:

```text

pedido interpretado por LPDB

          ↓

   integración Toast

          ↓

 precio/check de Toast

          ↓

 confirmación del cliente

          ↓

     pago en Toast

          ↓

    pago confirmado

          ↓

 Toast / fulfillment

          ↓

      KDS / cocina

```

LPDB no debe almacenar datos sensibles de tarjetas ni convertirse en procesador de pagos propio.

## 13.5 Toast y cocina

La integración deberá diseñarse para que, después de que el pedido esté correctamente creado y pagado según el flujo de Toast, Toast pueda ejecutar su flujo normal de fulfillment y envío a cocina/KDS cuando el restaurante tenga configurado el comportamiento correspondiente.

No se debe asumir que todo pedido será enviado automáticamente a cocina: esto depende de la configuración y capacidades de Toast/KDS del restaurante y deberá verificarse durante la integración.

## 13.6 Dashboard web del restaurante

Construir una interfaz web para operación y administración, no como requisito de descarga para el cliente.

Debe contemplar inicialmente:

- Pedidos.

- Detalle de pedidos.

- Estado de pedidos.

- Productos.

- Precios.

- Disponibilidad.

- Sedes.

- Configuración operativa necesaria.

## 13.7 Integración externa preparada

La fase debe definir contratos internos limpios para:

```text

LPDB Core

    ↓

Integration Layer

    ├── WhatsApp

    └── Toast

```

La implementación completa y endurecimiento de las integraciones externas continúa en la Fase 19 cuando corresponda.

## Principios arquitectónicos

1. **WhatsApp es la interfaz principal del cliente.**

2. **El dashboard web es la interfaz operativa del restaurante.**

3. **Toast es el sistema externo objetivo para POS y pagos; LPDB no implementa una pasarela propia.**

4. El backend FastAPI continúa siendo la fuente de verdad de la lógica de ordering de LPDB.

5. El frontend no duplica reglas de precios, disponibilidad o modificaciones.

6. El canal WhatsApp no debe contener lógica de negocio que deba vivir en los servicios del backend.

7. Las integraciones externas deben aislarse mediante una capa de integración.

8. No se implementará una app móvil nativa como requisito del producto salvo decisión explícita posterior.

## Backend existente que alimenta esta fase

Actualmente el backend dispone de piezas relevantes:

- `/agent/message`

- `/products/`

- búsqueda de productos

- consulta de recetas

- validación de modificaciones

- `/availability/{location_id}/{product_id}`

- `/orders/`

- `/orders/{id}`

Estas capacidades deben reutilizarse antes de crear nuevos endpoints.

## Lo que NO se debe asumir todavía

No se debe asumir sin decisión explícita:

- proveedor concreto de WhatsApp;

- credenciales de producción;

- permisos definitivos de Toast;

- configuración definitiva de Toast Payments;

- configuración de Toast KDS/auto-firing;

- autenticación definitiva del dashboard;

- infraestructura de producción.

## Criterio de cierre

La Fase 13 se considerará terminada cuando:

1. El canal de cliente definido esté técnicamente integrado o preparado según el alcance acordado.

2. El cliente pueda iniciar y continuar una conversación de ordering mediante WhatsApp.

3. El agente pueda interpretar y validar el pedido usando el backend existente.

4. El cliente pueda recibir y confirmar un resumen del pedido.

5. El pedido pueda prepararse para el flujo de pago mediante Toast sin crear una pasarela propia.

6. Exista un dashboard web operativo para el restaurante dentro del alcance acordado.

7. Exista una separación clara entre canal, interfaz operativa, backend y futuras integraciones externas.

8. Las pruebas de los flujos implementados pasen y exista un checkpoint de GitHub.

---

## FASE 14 — Pruebas integrales

**Estado:** COMPLETADA

### Alcance

- Pruebas del backend completo.

- Pruebas del dashboard.

- Pruebas del canal WhatsApp.

- Pruebas de integración canal ↔ API.

- Flujos End-to-End.

- Casos positivos y negativos.

- Regresiones de las Fases 10–13.

- Reducción de dependencia de pruebas manuales.

## FASE 15 — Autenticación y seguridad

**Estado:** COMPLETADA

### Alcance

- Autenticación.

- Usuarios.

- Roles.

- Autorización.

- Protección de endpoints administrativos.

- Protección de información sensible.

- CORS.

- Variables de entorno y secretos.

- Validación y controles de entrada.

- Seguridad de webhooks y callbacks.

## FASE 16 — Datos y migraciones de producción

**Estado:** COMPLETADA

### Alcance

- Revisión de migraciones Alembic.

- Seeds y datos iniciales.

- Integridad referencial.

- Constraints.

- Índices necesarios.

- Tratamiento de datos legacy.

- Backups y restauración.

- Estados de pedidos y pagos necesarios para producción.

- Flujo desarrollo → staging → producción.

## FASE 17 — Docker y despliegue

**Estado:** COMPLETADA

### Alcance

- Contenerización del backend.

- Configuración de ejecución para producción.

- Variables de entorno.

- Secrets.

- Health checks.

- Configuración de servicios.

- Preparación del dashboard para despliegue.

- Infraestructura necesaria para webhooks.

## FASE 18 — Staging

**Estado:** COMPLETADA

### Alcance

- Entorno de staging.

- Deploy de backend y dashboard.

- Base de datos de staging.

- Configuración independiente de producción.

- Pruebas desde Internet.

- Webhooks de prueba.

- Smoke tests.

- Correcciones antes de producción.

```text

GitHub

   ↓

STAGING

   ↓

PRUEBAS REALES

   ↓

CORRECCIONES

   ↓

PRODUCCIÓN

```

## FASE 19 — Integraciones externas

**Estado:** EN IMPLEMENTACIÓN AVANZADA — TOAST

### Estado real verificado en GitHub

La rama `feature/orderdb-tenant` ya contiene integración funcional y pruebas para submission, autenticación y construcción de payloads Toast. La fase no está en preparación inicial.

### Implementado y versionado

- Capa de integración externa separada del núcleo de ordering.
- Submission service y flujo E2E de envío a Toast.
- Pruebas de integración Toast, cobertura multi-tenant y rutas de fallo.
- Configuración Toast runtime por tenant.
- Autenticación Toast mediante client credentials.
- Cache de autenticación/token Toast por tenant.
- Construcción de payload operacional de órdenes Toast.
- Mapeos de productos y modificadores hacia Toast.
- Payloads Toast para modificadores.
- Persistencia de snapshots de precio y preservación del precio histórico.
- Propagación del identificador persistente de cada order item.
- Soporte de `BASE_CHANGE` con resolución del producto destino real.
- Persistencia de `new_product_id` y `new_product_name`.
- Migración Alembic para producto destino de `BASE_CHANGE`.
- Serialización y external mapping del producto destino.
- Fixtures y pruebas AREPA DE POLLO → PATACÓN DE POLLO.
- Resolución de `BASE_CHANGE` hasta el producto efectivo enviado a Toast.
- Resolución del mapping Toast correspondiente al producto destino de `BASE_CHANGE`.
- Integración de combos en el payload Toast.
- Resolución de papas de combo mediante mapping de ingrediente y `optionGroup`.
- Resolución de bebidas mediante mapping de producto y `productGroup`.
- Inclusión de papas y bebida como modifiers del selection Toast.
- Validación de mappings obligatorios para combos y bebidas.
- Aislamiento multi-tenant de mappings de combos y bebidas.
- Cobertura E2E de combos, bebidas y `BASE_CHANGE`.
- Regresión del bloque de payload fidelity validada con 112 pruebas aprobadas.

### Checkpoints recientes verificados

- `3a3b6e5` — complete Toast submission E2E integration.
- `eb17829` — align Toast integration tests.
- `8586bf5` — add multi-tenant isolation coverage.
- `420f5b7` — add failure path coverage.
- `ccbb512` — add multi-tenant Toast runtime configuration.
- `9c4dae9` — add Toast client credential authentication.
- `18c9a54` — cache Toast authentication per tenant.
- `1d11cd2` — build operational Toast order payload.
- `e58973e` — add Toast modifier mappings and payloads.
- `e1ad2e8` — persist and propagate base change target products.
- `76d642c` — resolve base change target product in Toast payload.
- `1a13959` — map combos and beverages into Toast payload.

### Avance de Toast payload fidelity

#### 19.12A — BASE_CHANGE → effective product → mapping → Toast payload

**Estado:** COMPLETADO

Implementado:

- Persistencia de `new_product_id` y `new_product_name`.
- Propagación del producto destino hasta el external order payload.
- Resolución del producto efectivo en `ToastOrderAdapter`.
- Resolución del mapping Toast del producto efectivo.
- Preservación del producto original dentro del dominio.
- Construcción del selection Toast utilizando el producto resultante.
- Validaciones de mappings faltantes y conflictos de `BASE_CHANGE`.
- Pruebas focalizadas y regresión satisfactorias.

**Checkpoint:** `76d642c` — `feat: resolve base change target product in Toast payload`

#### 19.12B — Combos + beverages → Toast payload

**Estado:** COMPLETADO

Implementado:

- Lectura del combo desde el external order payload.
- Resolución de `fries_ingredient_id`.
- Resolución del mapping Toast del ingrediente de papas.
- Resolución del `ingredient_group` correspondiente.
- Resolución de `beverage_product_id`.
- Resolución del mapping Toast de la bebida.
- Resolución del `product_group` correspondiente.
- Inclusión de papas y bebida como modifiers Toast.
- Propagación de la cantidad del combo.
- Validación de mappings faltantes.
- Aislamiento multi-tenant.
- Cobertura E2E específica.
- Actualización de Submission Service E2E.
- Actualización de Toast submission E2E.

Validación confirmada:

- `test_toast_combo_e2e.py`: 6 passed.
- `test_submission_toast_e2e.py`: 1 passed.
- `test_submission_service_with_toast.py`: 1 passed.
- Regresión Toast / Submission / External Mapping: 112 passed.
- 0 failed.
- `git diff --check`: limpio.

**Checkpoint:** `1a13959` — `feat: map combos and beverages into Toast payload`

#### 19.12 — Toast payload fidelity

**Estado:** COMPLETADO

La revisión del adapter confirma cobertura del modelo actualmente soportado para:

- Producto normal.
- Cantidad.
- `ADD`.
- `REMOVE`, que no genera modifier Toast por diseño.
- `BASE_CHANGE`.
- Combos.
- Papas de combo.
- Bebidas.
- Product mappings.
- Product group mappings.
- Ingredient mappings.
- Ingredient group mappings.
- Aislamiento de mappings por tenant.

No crear una subfase 19.12C sin evidencia técnica de un nuevo caso de payload no soportado.

### Punto exacto de continuidad

Frente activo: **19.13 — Toast responses, errors and retries**.

Los bloques `19.12A` y `19.12B` están completados y respaldados en GitHub.

El último checkpoint funcional confirmado es:

`1a13959` — `feat: map combos and beverages into Toast payload`

El siguiente trabajo debe revisar y endurecer el manejo de respuestas HTTP de Toast, clasificación de errores, fallos transitorios, reintentos seguros e idempotencia donde corresponda.

No reconstruir autenticación, routing, mappings, external order mapper ni payload fidelity ya terminados.

### Cierre de Fase 19

- 19.13 — COMPLETADA — Manejo de respuestas, errores, reintentos seguros e idempotencia Toast.
- 19.14 — COMPLETADA — Webhooks Toast multi-tenant, persistencia idempotente y reconciliación.
- 19.15 — COMPLETADA — Toast Payments, transporte, orquestación, mappings y validación E2E.
- 19.16 — COMPLETADA — Fulfillment/KDS, reconciliación, webhooks y ciclo hasta READY.
- 19.17 — COMPLETADA — Validación E2E integral y regresión completa de integraciones externas.
- 19.18 — COMPLETADA — Hardening final: concurrencia, prevención de duplicados, recuperación de fallos ambiguos, integridad de identificadores externos y aislamiento multi-tenant.

Validación final de Fase 19:

- Suite global: 611 pruebas aprobadas.
- Alembic: `310d4d26a1d6 (head)`.
- Hardening de mappings concurrentes completado.
- Prevención de doble envío de pagos completada.
- Recuperación segura ante timeout/5xx ambiguos completada.
- Aislamiento multi-tenant de integraciones externas validado.
- Working tree limpio al cierre técnico.

Checkpoint técnico de cierre previo a la actualización documental:

`835f071` — `harden ambiguous Toast payment recovery`

### Principio arquitectónico

```text
LPDB Core
   ↓
Integration Layer
   ├── WhatsApp
   └── Toast
          ├── Auth
          ├── Orders
          ├── Payments
          ├── Webhooks
          └── Fulfillment / KDS
```

Las integraciones externas no deben contaminar el núcleo de ordering.

### Criterio de cierre

Las integraciones de producción deben funcionar con autenticación, mapeo completo, manejo de errores, estados, reintentos cuando correspondan y pruebas E2E/regresión satisfactorias.

## FASE 20 — Observabilidad y operación

**Estado:** ACTUAL

### Alcance

- Logging.

- Manejo y seguimiento de errores.

- Health checks.

- Métricas.

- Monitoreo.

- Alertas.

- Auditoría.

- Seguimiento de webhooks, pagos y sincronización con POS.

**Estado: COMPLETADO / CERRADO**

Cierre validado:
- arquitectura autenticada y modular del dashboard;
- navegación desktop/mobile y responsive behavior;
- estados loading / empty / error;
- arquitectura preparada para usuario, tenant y role;
- regresión final: ESLint PASS, production build PASS, TypeScript PASS y Playwright E2E 5/5 PASS.

Commits de cierre:
- `8d55ad564afb853d51974ac072cf2b9cbbbd76a4` — responsive/accessibility;
- `87499d0ea89faed7637dba832ef9d4c7f02a85cf` — tenant/role-ready architecture.

**Punto de reanudación: 20.7 — Operación desde dashboard.**

## FASE 21 — Producción

**Estado:** PENDIENTE

### Alcance

- Deploy productivo.

- HTTPS.

- Dominio.

- Variables de producción.

- Base de datos productiva.

- Backups.

- Monitoring.

- Webhooks productivos.

- Configuración productiva de WhatsApp.

- Configuración productiva de Toast.

- Smoke tests.

- Prueba real de conversación → pedido → pago → POS/KDS.

### Criterio de cierre

El producto debe estar disponible públicamente y operar correctamente en un entorno productivo controlado.

## FASE 22 — Documentación y entrega

**Estado:** PENDIENTE

### Alcance

- README final.

- Arquitectura.

- Instalación.

- Variables de entorno.

- API.

- Base de datos.

- Migraciones.

- Dashboard.

- Canal WhatsApp.

- Toast.

- Deployment.

- Integraciones.

- Troubleshooting.

- Procedimientos operativos.

- Guía de administración del restaurante.

### Criterio de cierre

El proyecto debe poder ser instalado, entendido, operado y mantenido por otra persona sin depender de la memoria de esta conversación.

---

# MAPA RESUMIDO

```text

FASE 01 — Fundamentos del proyecto                    ✅

FASE 02 — API / CRUD inicial                          ✅

FASE 03 — PostgreSQL                                  ✅

FASE 04 — Modelado de catálogo                       ✅

FASE 05 — Productos / recetas                        ✅

FASE 06 — Sedes / disponibilidad                     ✅

FASE 07 — Modificaciones                              ✅

FASE 08 — Agent / Intent / conversación               ✅

FASE 09 — Integración completa ordering               ✅

FASE 10 — Precio final                                ✅

FASE 11 — Disponibilidad real                         ✅

FASE 12 — Consulta de pedidos                         ✅

FASE 13 — WhatsApp + Agent + Toast + Dashboard        ✅

FASE 14 — Pruebas integrales                          ✅

FASE 15 — Autenticación y seguridad                   ✅

FASE 16 — Datos / migraciones producción              ✅

FASE 17 — Docker / despliegue                         ✅

FASE 18 — Staging                                     ✅

FASE 19 — Integraciones externas                      ✅

FASE 20 — Observabilidad                              ▶️ ACTUAL

FASE 21 — Producción                                  ⏳

FASE 22 — Documentación / entrega                     ⏳

```

---

# CHECKPOINTS

| Fase | Estado | Checkpoint |

|---|---|---|

| 10 | COMPLETADA | Integrada en el estado funcional previo |

| 11 | COMPLETADA | Integrada en el estado funcional previo |

| 12 | COMPLETADA | `221116b` |

| Tenant Isolation | COMPLETADO | `333413d` |

| 13 | BASE FUNCIONAL IMPLEMENTADA | Integrada en rama de trabajo |
| 14 | COMPLETADA | Pruebas E2E, integración, multi-tenant, fallos y state machine versionadas |
| 15 | COMPLETADA | `54614ef`, `3102918`, `e4fe56a`, `66d1160` |
| 16 | COMPLETADA | `2b5f000`, `10f0c19`, `5258192`, `9394f26` |
| 17 | COMPLETADA | `055bc12`, `c17a702` |
| 18 | COMPLETADA | Cerrada y respaldada antes del inicio de Fase 19 |
| 19 | COMPLETADA | `835f071` + cierre formal de hardening y regresión |

---


---

# CHECKPOINT MAESTRO — INICIO FASE 20

Checkpoint de continuidad creado después del cierre formal de Fase 19.

## Estado consolidado del proyecto

- FASE 01 — Fundamentos — COMPLETADA
- FASE 02 — API / CRUD inicial — COMPLETADA
- FASE 03 — PostgreSQL — COMPLETADA
- FASE 04 — Modelado de catálogo — COMPLETADA
- FASE 05 — Productos / recetas — COMPLETADA
- FASE 06 — Locations / disponibilidad — COMPLETADA
- FASE 07 — Modificaciones — COMPLETADA
- FASE 08 — Agent / Intent / conversación — COMPLETADA
- FASE 09 — Ordering integration — COMPLETADA
- FASE 10 — Precio final — COMPLETADA
- FASE 11 — Disponibilidad real — COMPLETADA
- FASE 12 — Consulta de pedidos — COMPLETADA
- FASE 13 — WhatsApp + Agent + Toast + Dashboard base funcional — COMPLETADA
- FASE 14 — Pruebas integrales — COMPLETADA
- FASE 15 — Autenticación y seguridad — COMPLETADA
- FASE 16 — Datos / migraciones de producción — COMPLETADA
- FASE 17 — Docker / despliegue — COMPLETADA
- FASE 18 — Staging — COMPLETADA
- FASE 19 — Integraciones externas — COMPLETADA
- FASE 20 — Observabilidad, operación y dashboard operativo — ACTUAL
- FASE 21 — Producción — PENDIENTE
- FASE 22 — Documentación / entrega — PENDIENTE

## Cierre técnico confirmado de Fase 19

Checkpoint documental:

`f8cc731` — `docs: close phase 19 and start phase 20`

Checkpoint técnico anterior:

`835f071` — `harden ambiguous Toast payment recovery`

Validaciones acumuladas al cierre:

- Suite global confirmada: 611 pruebas aprobadas.
- Alembic: `310d4d26a1d6 (head)`.
- Toast Orders integrado.
- Toast Payments integrado.
- Toast Webhooks integrado.
- Fulfillment / KDS integrado.
- Reintentos seguros e idempotencia endurecidos.
- Recuperación de fallos ambiguos de pagos implementada.
- Prevención de duplicados concurrentes implementada.
- External mappings endurecidos contra carreras.
- Aislamiento multi-tenant validado.
- Validaciones E2E de integración completadas.
- Working tree limpio al cierre.
- Rama sincronizada con `origin/feature/orderdb-tenant`.

## Punto exacto de reanudación

La siguiente implementación comienza en:

**FASE 20 — Observabilidad, operación y dashboard operativo**

No reconstruir fases 01–19 salvo que una regresión demuestre un defecto real.

No reabrir Toast Orders, Payments, Webhooks, Fulfillment/KDS,
idempotencia, mappings o aislamiento multi-tenant sin evidencia técnica.

## Estado encontrado al iniciar Fase 20

Auditoría inicial:

- No se detectó infraestructura propia de logging estructurado en `app`.
- No se detectó infraestructura propia de métricas en `app`.
- No se detectaron health/readiness/liveness routes en `app`.
- Existe dashboard Next.js funcional.
- Dashboard usa Next.js 16.3.4.
- Dashboard usa React 19.2.8.
- Dashboard tiene Playwright.
- Existen pruebas E2E de dashboard para canales, pedidos y estados.

## Plan de ejecución de Fase 20

### 20.1 — Observability foundation

Implementar:

- logging estructurado;
- request/correlation IDs;
- tenant context en eventos operativos;
- clasificación consistente de errores;
- eventos operativos relevantes;
- protección contra exposición de secretos o datos sensibles.

### 20.2 — Health / readiness / liveness

Implementar:

- health check de API;
- readiness de base de datos;
- liveness;
- estado de dependencias críticas cuando corresponda;
- respuestas aptas para infraestructura y monitoreo.

### 20.3 — Métricas operativas

Medir como mínimo:

- órdenes;
- órdenes exitosas/fallidas;
- pagos;
- pagos exitosos/fallidos;
- Toast submissions;
- WhatsApp processing;
- webhooks;
- retries;
- reconciliaciones;
- latencias;
- errores por integración y tenant.

### 20.4 — Alertas e incidentes

Definir condiciones operativas para:

- errores repetidos;
- integración caída;
- fallos de pagos;
- órdenes atascadas;
- reconciliaciones pendientes;
- webhooks fallidos;
- degradación de servicios.

### 20.5 — Operational data layer

Crear servicios/endpoints necesarios para que el dashboard consuma
información operativa real sin acoplarse directamente a detalles internos
de proveedores externos.

## CHECKPOINT — CIERRE 20.5 OPERATIONAL DATA LAYER

Estado: **COMPLETADA / CERRADA**

Implementado:

- persistencia PostgreSQL de incidentes operativos;
- migraci?n Alembic `e5374cc233ec`;
- servicio persistente de incidentes;
- integraci?n monitor ? almacenamiento persistente;
- worker/runtime autom?tico del monitor operacional;
- API multi-tenant de incidentes para dashboard;
- aislamiento por tenant en m?tricas, fingerprints e incidentes;
- prevenci?n de re-disparo de incidentes por series m?tricas no relacionadas;
- identidad persistente estable de `incident_id` en upserts por fingerprint;
- permisos de lectura mediante `VIEW_DASHBOARD`.

Validaci?n final:

- Suite global: **712 passed**.
- Alembic current: `e5374cc233ec (head)`.
- Alembic heads: `e5374cc233ec (head)`.
- `git diff --check`: sin errores.
- Hardening t?cnico respaldado en commit:
  `d8aa066d3603b7c14daddc94a737ac96c3906193`.

Punto exacto de reanudaci?n:

**20.6 — Arquitectura final del dashboard**

No reabrir 20.5 salvo que una regresi?n demuestre un defecto real.

---

### 20.6 — Arquitectura final del dashboard

Definir y construir:

- navegación;
- layout;
- responsive behavior;
- jerarquía de información;
- estados loading / empty / error;
- permisos y visibilidad por rol/tenant.

### 20.7 — Operación desde dashboard

Incluir:

- pedidos;
- estados;
- pagos;
- clientes;
- integraciones;
- errores;
- alertas;
- actividad operativa;
- acciones seguras cuando correspondan.

### 20.8 — Métricas de negocio

Incluir como mínimo:

- ventas;
- volumen de órdenes;
- ticket promedio;
- evolución temporal;
- performance por restaurante/location;
- estados y conversiones operativas disponibles.

### 20.9 — Administración

Incluir:

- configuración del restaurante;
- locations;
- usuarios;
- roles/permisos;
- integraciones;
- estado de configuración.

### 20.10 — Finalización y regresión de Fase 20

Completar:

- diseño visual final;
- responsive;
- accesibilidad básica;
- manejo de errores;
- pruebas backend;
- pruebas frontend;
- pruebas E2E;
- regresión integral;
- checkpoint final antes de Fase 21.

## Disciplina de trabajo para Fase 20

Cada subfase debe seguir:

1. Inspeccionar primero el código existente.
2. No duplicar funcionalidades ya implementadas.
3. Implementar el bloque completo.
4. Ejecutar pruebas específicas.
5. Ejecutar regresión relacionada.
6. Revisar `git diff --check`.
7. Confirmar `git status`.
8. Hacer commit descriptivo.
9. Hacer push a `feature/orderdb-tenant`.
10. Confirmar SHA remoto.
11. Actualizar ROADMAP solamente cuando cambie el estado real del proyecto.

No declarar una subfase completada si las pruebas correspondientes no han sido ejecutadas satisfactoriamente.

No crear subfases adicionales sin evidencia técnica.

---
# DISCIPLINA DE CHECKPOINTS Y CONTINUIDAD

Desde este checkpoint, **guardar el trabajo** significa sincronizar código y memoria técnica del proyecto.

En cada cierre de bloque significativo:

1. Ejecutar las pruebas correspondientes.
2. Confirmar `git status`.
3. Actualizar este ROADMAP si cambió fase, subfase, alcance, checkpoint o punto de continuidad.
4. Crear commit del código/documentación.
5. Hacer push a `feature/orderdb-tenant`.
6. Confirmar el SHA remoto.
7. Registrar el siguiente punto exacto de trabajo cuando exista un cambio material.

El historial Git es la evidencia técnica y este ROADMAP es el índice de continuidad. Ambos deben permanecer alineados.

---

# REGLA DE CONTINUIDAD

Antes de comenzar cualquier nueva fase se debe revisar este archivo y el estado actual de Git.

Antes de cerrar una fase se debe:

1. Ejecutar las pruebas correspondientes.

2. Revisar los cambios de código.

3. Actualizar este `ROADMAP.md`.

4. Crear un commit de checkpoint.

5. Hacer `git push` sobre la rama de trabajo correspondiente y verificar que el checkpoint quede respaldado en GitHub.

6. Verificar que el working tree quede limpio.

El siguiente trabajo comienza siempre desde el último checkpoint confirmado en este documento y en GitHub.