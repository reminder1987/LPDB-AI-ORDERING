# LPDB-AI-ORDERING â€” ROADMAP OFICIAL

## Fuente de verdad del proyecto

Este documento es la fuente oficial del orden, alcance y estado de las fases del proyecto.

### Reglas del roadmap

1. Las fases mantienen el orden establecido en este documento.

2. No se deben renumerar, eliminar, fusionar ni crear fases nuevas sin actualizar primero este documento.

3. Al cerrar una fase se debe actualizar su estado y registrar el checkpoint de Git correspondiente.

4. Cada fase debe tener objetivo, alcance, pruebas y criterio de cierre antes de marcarse como completada.

5. Si la conversaciÃ³n y este documento presentan una contradicciÃ³n, primero se revisa el repositorio y se actualiza este documento de forma explÃ­cita antes de continuar.

6. El cÃ³digo de producciÃ³n debe permanecer alineado con el roadmap y cada hito importante debe quedar versionado en GitHub.

---

# ESTADO ACTUAL

Fase actual: 19 â€” Integraciones externas

Estado: EN IMPLEMENTACIÃ“N AVANZADA â€” TOAST

Base funcional previa: ordering, conversaciÃ³n/agente, multi-tenant, canales y submission E2E ya implementados.

Hito transversal completado: Tenant Isolation

Ãšltimo checkpoint funcional confirmado: 1a13959 â€” map combos and beverages into Toast payload

Rama de trabajo actual: feature/orderdb-tenant

Rama principal: master

---

# FASES DEL PROYECTO

## FASE 01 â€” Fundamentos del proyecto

**Estado:** COMPLETADA

## FASE 02 â€” API / CRUD inicial

**Estado:** COMPLETADA

## FASE 03 â€” PostgreSQL

**Estado:** COMPLETADA

## FASE 04 â€” Modelado de catÃ¡logo

**Estado:** COMPLETADA

## FASE 05 â€” Productos / recetas

**Estado:** COMPLETADA

## FASE 06 â€” Sedes / disponibilidad

**Estado:** COMPLETADA

## FASE 07 â€” Modificaciones

**Estado:** COMPLETADA

Reglas y persistencia de `ADD`, `REMOVE` y `BASE_CHANGE`.

## FASE 08 â€” Agent / Intent / conversaciÃ³n

**Estado:** COMPLETADA

InterpretaciÃ³n de mensajes, productos, cantidades, modificaciones, combos y flujo conversacional.

## FASE 09 â€” IntegraciÃ³n completa de ordering

**Estado:** COMPLETADA

IntegraciÃ³n de catÃ¡logo, modificaciones, disponibilidad, sedes, conversaciÃ³n y persistencia.

## FASE 10 â€” Precio final

**Estado:** COMPLETADA

- Precio base de productos.

- Precio de `ADD`.

- `REMOVE` sin costo adicional.

- `BASE_CHANGE` segÃºn producto/base resultante.

- Cantidades.

- MÃºltiples productos.

- Combos y bebida.

- Subtotal y total consistentes.

- No inventar precios de combo mientras no estÃ©n definidos.

## FASE 11 â€” Disponibilidad real

**Estado:** COMPLETADA

- Producto disponible/no disponible.

- Ingredientes y modificaciones segÃºn disponibilidad.

- Bebidas disponibles.

- ValidaciÃ³n antes de crear la orden.

- IntegraciÃ³n con el flujo conversacional.

## FASE 12 â€” Consulta de pedidos

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

- MÃºltiples items.

- Combos y bebidas.

- Precio de combo.

- `unit_price`, `subtotal` y `total`.

- `404` para pedido inexistente.

### Checkpoint

`221116b` â€” `feat: completar consultas de pedidos fase 12`

---

# HITO TRANSVERSAL â€” TENANT ISOLATION

Estado: COMPLETADO

Este hito establece el aislamiento multi-tenant transversal del backend antes de avanzar hacia la capa de interacciÃ³n del producto.

## Alcance implementado

ResoluciÃ³n del tenant mediante el header HTTP X-Tenant.

TenantContext como contexto de negocio.

Tenant obligatorio en los endpoints protegidos.

ValidaciÃ³n de tenant inexistente o inactivo.

PropagaciÃ³n del tenant_id desde la capa HTTP hacia los servicios.

Aislamiento de productos por tenant.

Aislamiento de disponibilidad por tenant.

Aislamiento de sedes por tenant.

Aislamiento de Ã³rdenes y sesiones conversacionales por tenant.

Validaciones de disponibilidad conscientes de tenant.

Persistencia de tenant_id donde corresponde en el dominio de ordering.

## Validaciones realizadas

GET /products/ con X-Tenant: lpdb â†’ correcto.

GET /products/ sin X-Tenant â†’ rechazado.

GET /products/ con tenant inexistente â†’ rechazado.

GET /availability/1/1 con X-Tenant: lpdb â†’ correcto.

GET /availability/1/1 sin X-Tenant â†’ rechazado.

VerificaciÃ³n de consistencia entre ingredientes y sedes.

Pruebas del flujo conversacional con tenant.

CompilaciÃ³n de los mÃ³dulos API modificados.

git diff --check â†’ limpio.

## Checkpoints Git

a9f290b â€” Add tenant context to conversation orders

333413d â€” Enforce tenant context on product and availability APIs

## Criterio de cierre

El backend cuenta con un contexto de tenant explÃ­cito y las APIs auditadas no pueden operar sin un tenant vÃ¡lido. El hito queda cerrado y respaldado en GitHub.

---

# FASE 13 â€” Canal de cliente, agente IA y dashboard operativo

**Estado:** BASE FUNCIONAL IMPLEMENTADA

## Objetivo

Construir la capa de interacciÃ³n del producto alrededor de la visiÃ³n real del negocio:

> El cliente no necesita descargar una aplicaciÃ³n nueva. El canal principal del cliente serÃ¡ WhatsApp, donde conversa con el agente de IA. El agente entiende y valida el pedido, confirma la orden y conduce el flujo hasta el pago mediante Toast. Una vez confirmado el pago, el pedido queda listo para el flujo operativo de Toast y su envÃ­o a cocina/KDS segÃºn la configuraciÃ³n del restaurante.

La interfaz web no serÃ¡ el frontend principal del cliente. El frontend web de esta fase serÃ¡ principalmente un **dashboard operativo para el restaurante/administrador**.

## Arquitectura conceptual

```text

Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  CLIENTE

Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â â”‚

Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â â”‚ WhatsApp

Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â â–¼

Â  Â  Â  Â  Â  Â  Â  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”

Â  Â  Â  Â  Â  Â  Â  â”‚ Â AGENTE DE IA Â  â”‚

Â  Â  Â  Â  Â  Â  Â  â”‚ Â  Â WHATSAPP Â  Â  â”‚

Â  Â  Â  Â  Â  Â  Â  â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜

Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â â”‚

Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â â–¼

Â  Â  Â  Â  Â  Â  Â  CATÃLOGO / PRECIOS

Â  Â  Â  Â  Â  Â  Â  DISPONIBILIDAD

Â  Â  Â  Â  Â  Â  Â  MODIFICACIONES

Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â â”‚

Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â â–¼

Â  Â  Â  Â  Â  Â  Â  Â  Â CONFIRMA ORDEN

Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â â”‚

Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â â–¼

Â  Â  Â  Â  Â  Â  Â  Â  Â INTEGRACIÃ“N TOAST

Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â â”‚

Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â â–¼

Â  Â  Â  Â  Â  Â  Â  Â  Â  PAGO EN TOAST

Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â â”‚

Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â â–¼

Â  Â  Â  Â  Â  Â  Â  Â  ORDEN PAGADA

Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â â”‚

Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â â–¼

Â  Â  Â  Â  Â  Â  Â  Â  Â TOAST / KDS

Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â â”‚

Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â â–¼

Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  COCINA

```

En paralelo:

```text

RESTAURANTE

Â  Â  Â â”‚

Â  Â  Â â–¼

DASHBOARD WEB

Â  Â  Â â”‚

Â  Â  Â â”œâ”€â”€ Pedidos

Â  Â  Â â”œâ”€â”€ Productos

Â  Â  Â â”œâ”€â”€ Precios

Â  Â  Â â”œâ”€â”€ Disponibilidad

Â  Â  Â â”œâ”€â”€ Sedes

Â  Â  Â â””â”€â”€ ConfiguraciÃ³n

```

## 13.1 Canal WhatsApp

Definir e implementar el canal mediante el cual los clientes conversarÃ¡n con el agente sin instalar una aplicaciÃ³n nueva.

Debe contemplar:

- RecepciÃ³n de mensajes.

- EnvÃ­o de respuestas.

- IdentificaciÃ³n de cliente/conversaciÃ³n.

- Persistencia de sesiÃ³n.

- Manejo de errores del canal.

- ConfirmaciÃ³n conversacional del pedido.

El proveedor concreto de WhatsApp queda pendiente de decisiÃ³n tÃ©cnica antes de implementar la integraciÃ³n.

## 13.2 Agente de IA / conversaciÃ³n

Reutilizar el motor existente de `/agent/message` y `conversation_service` como nÃºcleo de interpretaciÃ³n y conversaciÃ³n.

El canal externo no debe duplicar la lÃ³gica de intent, modificaciones, disponibilidad ni precios.

## 13.3 ConfirmaciÃ³n del pedido

El cliente debe recibir una representaciÃ³n clara del pedido antes del pago, incluyendo cuando corresponda:

- Productos.

- Cantidades.

- Modificaciones.

- Combos.

- Bebidas.

- Subtotal.

- Total.

## 13.4 Toast como sistema de pago y POS

**No se construirÃ¡ una pasarela de pagos propia para el producto.**

La arquitectura objetivo es integrar Toast para que el pedido pueda entrar en su ecosistema de POS/pagos. Toast serÃ¡ la referencia externa para el precio final y el flujo de pago, sujeto a los permisos, capacidades y configuraciÃ³n del restaurante y de la integraciÃ³n aprobada por Toast.

Flujo objetivo:

```text

pedido interpretado por LPDB

Â  Â  Â  Â  Â  â†“

Â  Â integraciÃ³n Toast

Â  Â  Â  Â  Â  â†“

Â precio/check de Toast

Â  Â  Â  Â  Â  â†“

Â confirmaciÃ³n del cliente

Â  Â  Â  Â  Â  â†“

Â  Â  Â pago en Toast

Â  Â  Â  Â  Â  â†“

Â  Â  pago confirmado

Â  Â  Â  Â  Â  â†“

Â Toast / fulfillment

Â  Â  Â  Â  Â  â†“

Â  Â  Â  KDS / cocina

```

LPDB no debe almacenar datos sensibles de tarjetas ni convertirse en procesador de pagos propio.

## 13.5 Toast y cocina

La integraciÃ³n deberÃ¡ diseÃ±arse para que, despuÃ©s de que el pedido estÃ© correctamente creado y pagado segÃºn el flujo de Toast, Toast pueda ejecutar su flujo normal de fulfillment y envÃ­o a cocina/KDS cuando el restaurante tenga configurado el comportamiento correspondiente.

No se debe asumir que todo pedido serÃ¡ enviado automÃ¡ticamente a cocina: esto depende de la configuraciÃ³n y capacidades de Toast/KDS del restaurante y deberÃ¡ verificarse durante la integraciÃ³n.

## 13.6 Dashboard web del restaurante

Construir una interfaz web para operaciÃ³n y administraciÃ³n, no como requisito de descarga para el cliente.

Debe contemplar inicialmente:

- Pedidos.

- Detalle de pedidos.

- Estado de pedidos.

- Productos.

- Precios.

- Disponibilidad.

- Sedes.

- ConfiguraciÃ³n operativa necesaria.

## 13.7 IntegraciÃ³n externa preparada

La fase debe definir contratos internos limpios para:

```text

LPDB Core

Â  Â  â†“

Integration Layer

Â  Â  â”œâ”€â”€ WhatsApp

Â  Â  â””â”€â”€ Toast

```

La implementaciÃ³n completa y endurecimiento de las integraciones externas continÃºa en la Fase 19 cuando corresponda.

## Principios arquitectÃ³nicos

1. **WhatsApp es la interfaz principal del cliente.**

2. **El dashboard web es la interfaz operativa del restaurante.**

3. **Toast es el sistema externo objetivo para POS y pagos; LPDB no implementa una pasarela propia.**

4. El backend FastAPI continÃºa siendo la fuente de verdad de la lÃ³gica de ordering de LPDB.

5. El frontend no duplica reglas de precios, disponibilidad o modificaciones.

6. El canal WhatsApp no debe contener lÃ³gica de negocio que deba vivir en los servicios del backend.

7. Las integraciones externas deben aislarse mediante una capa de integraciÃ³n.

8. No se implementarÃ¡ una app mÃ³vil nativa como requisito del producto salvo decisiÃ³n explÃ­cita posterior.

## Backend existente que alimenta esta fase

Actualmente el backend dispone de piezas relevantes:

- `/agent/message`

- `/products/`

- bÃºsqueda de productos

- consulta de recetas

- validaciÃ³n de modificaciones

- `/availability/{location_id}/{product_id}`

- `/orders/`

- `/orders/{id}`

Estas capacidades deben reutilizarse antes de crear nuevos endpoints.

## Lo que NO se debe asumir todavÃ­a

No se debe asumir sin decisiÃ³n explÃ­cita:

- proveedor concreto de WhatsApp;

- credenciales de producciÃ³n;

- permisos definitivos de Toast;

- configuraciÃ³n definitiva de Toast Payments;

- configuraciÃ³n de Toast KDS/auto-firing;

- autenticaciÃ³n definitiva del dashboard;

- infraestructura de producciÃ³n.

## Criterio de cierre

La Fase 13 se considerarÃ¡ terminada cuando:

1. El canal de cliente definido estÃ© tÃ©cnicamente integrado o preparado segÃºn el alcance acordado.

2. El cliente pueda iniciar y continuar una conversaciÃ³n de ordering mediante WhatsApp.

3. El agente pueda interpretar y validar el pedido usando el backend existente.

4. El cliente pueda recibir y confirmar un resumen del pedido.

5. El pedido pueda prepararse para el flujo de pago mediante Toast sin crear una pasarela propia.

6. Exista un dashboard web operativo para el restaurante dentro del alcance acordado.

7. Exista una separaciÃ³n clara entre canal, interfaz operativa, backend y futuras integraciones externas.

8. Las pruebas de los flujos implementados pasen y exista un checkpoint de GitHub.

---

## FASE 14 â€” Pruebas integrales

**Estado:** COMPLETADA

### Alcance

- Pruebas del backend completo.

- Pruebas del dashboard.

- Pruebas del canal WhatsApp.

- Pruebas de integraciÃ³n canal â†” API.

- Flujos End-to-End.

- Casos positivos y negativos.

- Regresiones de las Fases 10â€“13.

- ReducciÃ³n de dependencia de pruebas manuales.

## FASE 15 â€” AutenticaciÃ³n y seguridad

**Estado:** COMPLETADA

### Alcance

- AutenticaciÃ³n.

- Usuarios.

- Roles.

- AutorizaciÃ³n.

- ProtecciÃ³n de endpoints administrativos.

- ProtecciÃ³n de informaciÃ³n sensible.

- CORS.

- Variables de entorno y secretos.

- ValidaciÃ³n y controles de entrada.

- Seguridad de webhooks y callbacks.

## FASE 16 â€” Datos y migraciones de producciÃ³n

**Estado:** COMPLETADA

### Alcance

- RevisiÃ³n de migraciones Alembic.

- Seeds y datos iniciales.

- Integridad referencial.

- Constraints.

- Ãndices necesarios.

- Tratamiento de datos legacy.

- Backups y restauraciÃ³n.

- Estados de pedidos y pagos necesarios para producciÃ³n.

- Flujo desarrollo â†’ staging â†’ producciÃ³n.

## FASE 17 â€” Docker y despliegue

**Estado:** COMPLETADA

### Alcance

- ContenerizaciÃ³n del backend.

- ConfiguraciÃ³n de ejecuciÃ³n para producciÃ³n.

- Variables de entorno.

- Secrets.

- Health checks.

- ConfiguraciÃ³n de servicios.

- PreparaciÃ³n del dashboard para despliegue.

- Infraestructura necesaria para webhooks.

## FASE 18 â€” Staging

**Estado:** COMPLETADA

### Alcance

- Entorno de staging.

- Deploy de backend y dashboard.

- Base de datos de staging.

- ConfiguraciÃ³n independiente de producciÃ³n.

- Pruebas desde Internet.

- Webhooks de prueba.

- Smoke tests.

- Correcciones antes de producciÃ³n.

```text

GitHub

Â  Â â†“

STAGING

Â  Â â†“

PRUEBAS REALES

Â  Â â†“

CORRECCIONES

Â  Â â†“

PRODUCCIÃ“N

```

## FASE 19 â€” Integraciones externas

**Estado:** EN IMPLEMENTACIÃ“N AVANZADA â€” TOAST

### Estado real verificado en GitHub

La rama `feature/orderdb-tenant` ya contiene integraciÃ³n funcional y pruebas para submission, autenticaciÃ³n y construcciÃ³n de payloads Toast. La fase no estÃ¡ en preparaciÃ³n inicial.

### Implementado y versionado

- Capa de integraciÃ³n externa separada del nÃºcleo de ordering.
- Submission service y flujo E2E de envÃ­o a Toast.
- Pruebas de integraciÃ³n Toast, cobertura multi-tenant y rutas de fallo.
- ConfiguraciÃ³n Toast runtime por tenant.
- AutenticaciÃ³n Toast mediante client credentials.
- Cache de autenticaciÃ³n/token Toast por tenant.
- ConstrucciÃ³n de payload operacional de Ã³rdenes Toast.
- Mapeos de productos y modificadores hacia Toast.
- Payloads Toast para modificadores.
- Persistencia de snapshots de precio y preservaciÃ³n del precio histÃ³rico.
- PropagaciÃ³n del identificador persistente de cada order item.
- Soporte de `BASE_CHANGE` con resoluciÃ³n del producto destino real.
- Persistencia de `new_product_id` y `new_product_name`.
- MigraciÃ³n Alembic para producto destino de `BASE_CHANGE`.
- SerializaciÃ³n y external mapping del producto destino.
- Fixtures y pruebas AREPA DE POLLO â†’ PATACÃ“N DE POLLO.
- ResoluciÃ³n de `BASE_CHANGE` hasta el producto efectivo enviado a Toast.
- ResoluciÃ³n del mapping Toast correspondiente al producto destino de `BASE_CHANGE`.
- IntegraciÃ³n de combos en el payload Toast.
- ResoluciÃ³n de papas de combo mediante mapping de ingrediente y `optionGroup`.
- ResoluciÃ³n de bebidas mediante mapping de producto y `productGroup`.
- InclusiÃ³n de papas y bebida como modifiers del selection Toast.
- ValidaciÃ³n de mappings obligatorios para combos y bebidas.
- Aislamiento multi-tenant de mappings de combos y bebidas.
- Cobertura E2E de combos, bebidas y `BASE_CHANGE`.
- RegresiÃ³n del bloque de payload fidelity validada con 112 pruebas aprobadas.

### Checkpoints recientes verificados

- `3a3b6e5` â€” complete Toast submission E2E integration.
- `eb17829` â€” align Toast integration tests.
- `8586bf5` â€” add multi-tenant isolation coverage.
- `420f5b7` â€” add failure path coverage.
- `ccbb512` â€” add multi-tenant Toast runtime configuration.
- `9c4dae9` â€” add Toast client credential authentication.
- `18c9a54` â€” cache Toast authentication per tenant.
- `1d11cd2` â€” build operational Toast order payload.
- `e58973e` â€” add Toast modifier mappings and payloads.
- `e1ad2e8` â€” persist and propagate base change target products.
- `76d642c` â€” resolve base change target product in Toast payload.
- `1a13959` â€” map combos and beverages into Toast payload.

### Avance de Toast payload fidelity

#### 19.12A â€” BASE_CHANGE â†’ effective product â†’ mapping â†’ Toast payload

**Estado:** COMPLETADO

Implementado:

- Persistencia de `new_product_id` y `new_product_name`.
- PropagaciÃ³n del producto destino hasta el external order payload.
- ResoluciÃ³n del producto efectivo en `ToastOrderAdapter`.
- ResoluciÃ³n del mapping Toast del producto efectivo.
- PreservaciÃ³n del producto original dentro del dominio.
- ConstrucciÃ³n del selection Toast utilizando el producto resultante.
- Validaciones de mappings faltantes y conflictos de `BASE_CHANGE`.
- Pruebas focalizadas y regresiÃ³n satisfactorias.

**Checkpoint:** `76d642c` â€” `feat: resolve base change target product in Toast payload`

#### 19.12B â€” Combos + beverages â†’ Toast payload

**Estado:** COMPLETADO

Implementado:

- Lectura del combo desde el external order payload.
- ResoluciÃ³n de `fries_ingredient_id`.
- ResoluciÃ³n del mapping Toast del ingrediente de papas.
- ResoluciÃ³n del `ingredient_group` correspondiente.
- ResoluciÃ³n de `beverage_product_id`.
- ResoluciÃ³n del mapping Toast de la bebida.
- ResoluciÃ³n del `product_group` correspondiente.
- InclusiÃ³n de papas y bebida como modifiers Toast.
- PropagaciÃ³n de la cantidad del combo.
- ValidaciÃ³n de mappings faltantes.
- Aislamiento multi-tenant.
- Cobertura E2E especÃ­fica.
- ActualizaciÃ³n de Submission Service E2E.
- ActualizaciÃ³n de Toast submission E2E.

ValidaciÃ³n confirmada:

- `test_toast_combo_e2e.py`: 6 passed.
- `test_submission_toast_e2e.py`: 1 passed.
- `test_submission_service_with_toast.py`: 1 passed.
- RegresiÃ³n Toast / Submission / External Mapping: 112 passed.
- 0 failed.
- `git diff --check`: limpio.

**Checkpoint:** `1a13959` â€” `feat: map combos and beverages into Toast payload`

#### 19.12 â€” Toast payload fidelity

**Estado:** COMPLETADO

La revisiÃ³n del adapter confirma cobertura del modelo actualmente soportado para:

- Producto normal.
- Cantidad.
- `ADD`.
- `REMOVE`, que no genera modifier Toast por diseÃ±o.
- `BASE_CHANGE`.
- Combos.
- Papas de combo.
- Bebidas.
- Product mappings.
- Product group mappings.
- Ingredient mappings.
- Ingredient group mappings.
- Aislamiento de mappings por tenant.

No crear una subfase 19.12C sin evidencia tÃ©cnica de un nuevo caso de payload no soportado.

### Punto exacto de continuidad

Frente activo: **19.13 â€” Toast responses, errors and retries**.

Los bloques `19.12A` y `19.12B` estÃ¡n completados y respaldados en GitHub.

El Ãºltimo checkpoint funcional confirmado es:

`1a13959` â€” `feat: map combos and beverages into Toast payload`

El siguiente trabajo debe revisar y endurecer el manejo de respuestas HTTP de Toast, clasificaciÃ³n de errores, fallos transitorios, reintentos seguros e idempotencia donde corresponda.

No reconstruir autenticaciÃ³n, routing, mappings, external order mapper ni payload fidelity ya terminados.

### Cierre de Fase 19

- 19.13 â€” COMPLETADA â€” Manejo de respuestas, errores, reintentos seguros e idempotencia Toast.
- 19.14 â€” COMPLETADA â€” Webhooks Toast multi-tenant, persistencia idempotente y reconciliaciÃ³n.
- 19.15 â€” COMPLETADA â€” Toast Payments, transporte, orquestaciÃ³n, mappings y validaciÃ³n E2E.
- 19.16 â€” COMPLETADA â€” Fulfillment/KDS, reconciliaciÃ³n, webhooks y ciclo hasta READY.
- 19.17 â€” COMPLETADA â€” ValidaciÃ³n E2E integral y regresiÃ³n completa de integraciones externas.
- 19.18 â€” COMPLETADA â€” Hardening final: concurrencia, prevenciÃ³n de duplicados, recuperaciÃ³n de fallos ambiguos, integridad de identificadores externos y aislamiento multi-tenant.

ValidaciÃ³n final de Fase 19:

- Suite global: 611 pruebas aprobadas.
- Alembic: `310d4d26a1d6 (head)`.
- Hardening de mappings concurrentes completado.
- PrevenciÃ³n de doble envÃ­o de pagos completada.
- RecuperaciÃ³n segura ante timeout/5xx ambiguos completada.
- Aislamiento multi-tenant de integraciones externas validado.
- Working tree limpio al cierre tÃ©cnico.

Checkpoint tÃ©cnico de cierre previo a la actualizaciÃ³n documental:

`835f071` â€” `harden ambiguous Toast payment recovery`

### Principio arquitectÃ³nico

```text
LPDB Core
   â†“
Integration Layer
   â”œâ”€â”€ WhatsApp
   â””â”€â”€ Toast
          â”œâ”€â”€ Auth
          â”œâ”€â”€ Orders
          â”œâ”€â”€ Payments
          â”œâ”€â”€ Webhooks
          â””â”€â”€ Fulfillment / KDS
```

Las integraciones externas no deben contaminar el nÃºcleo de ordering.

### Criterio de cierre

Las integraciones de producciÃ³n deben funcionar con autenticaciÃ³n, mapeo completo, manejo de errores, estados, reintentos cuando correspondan y pruebas E2E/regresiÃ³n satisfactorias.

## FASE 20 â€” Observabilidad y operaciÃ³n

**Estado:** ACTUAL

### Alcance

- Logging.

- Manejo y seguimiento de errores.

- Health checks.

- MÃ©tricas.

- Monitoreo.

- Alertas.

- AuditorÃ­a.

- Seguimiento de webhooks, pagos y sincronizaciÃ³n con POS.

## FASE 21 â€” ProducciÃ³n

**Estado:** PENDIENTE

### Alcance

- Deploy productivo.

- HTTPS.

- Dominio.

- Variables de producciÃ³n.

- Base de datos productiva.

- Backups.

- Monitoring.

- Webhooks productivos.

- ConfiguraciÃ³n productiva de WhatsApp.

- ConfiguraciÃ³n productiva de Toast.

- Smoke tests.

- Prueba real de conversaciÃ³n â†’ pedido â†’ pago â†’ POS/KDS.

### Criterio de cierre

El producto debe estar disponible pÃºblicamente y operar correctamente en un entorno productivo controlado.

## FASE 22 â€” DocumentaciÃ³n y entrega

**Estado:** PENDIENTE

### Alcance

- README final.

- Arquitectura.

- InstalaciÃ³n.

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

- GuÃ­a de administraciÃ³n del restaurante.

### Criterio de cierre

El proyecto debe poder ser instalado, entendido, operado y mantenido por otra persona sin depender de la memoria de esta conversaciÃ³n.

---

# MAPA RESUMIDO

```text

FASE 01 â€” Fundamentos del proyecto Â  Â  Â  Â  Â  Â  Â  Â  Â  Â âœ…

FASE 02 â€” API / CRUD inicial Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â âœ…

FASE 03 â€” PostgreSQL Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â âœ…

FASE 04 â€” Modelado de catÃ¡logo Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  âœ…

FASE 05 â€” Productos / recetas Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â âœ…

FASE 06 â€” Sedes / disponibilidad Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  âœ…

FASE 07 â€” Modificaciones Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â âœ…

FASE 08 â€” Agent / Intent / conversaciÃ³n Â  Â  Â  Â  Â  Â  Â  âœ…

FASE 09 â€” IntegraciÃ³n completa ordering Â  Â  Â  Â  Â  Â  Â  âœ…

FASE 10 â€” Precio final Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â âœ…

FASE 11 â€” Disponibilidad real Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  âœ…

FASE 12 â€” Consulta de pedidos Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  âœ…

FASE 13 â€” WhatsApp + Agent + Toast + Dashboard        âœ…

FASE 14 â€” Pruebas integrales                          âœ…

FASE 15 â€” AutenticaciÃ³n y seguridad                   âœ…

FASE 16 â€” Datos / migraciones producciÃ³n              âœ…

FASE 17 â€” Docker / despliegue                         âœ…

FASE 18 â€” Staging                                     âœ…

FASE 19 â€” Integraciones externas                      âœ…

FASE 20 â€” Observabilidad                              â–¶ï¸ ACTUAL

FASE 21 â€” ProducciÃ³n Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  Â â³

FASE 22 â€” DocumentaciÃ³n / entrega Â  Â  Â  Â  Â  Â  Â  Â  Â  Â  â³

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
| 14 | COMPLETADA | Pruebas E2E, integraciÃ³n, multi-tenant, fallos y state machine versionadas |
| 15 | COMPLETADA | `54614ef`, `3102918`, `e4fe56a`, `66d1160` |
| 16 | COMPLETADA | `2b5f000`, `10f0c19`, `5258192`, `9394f26` |
| 17 | COMPLETADA | `055bc12`, `c17a702` |
| 18 | COMPLETADA | Cerrada y respaldada antes del inicio de Fase 19 |
| 19 | COMPLETADA | `835f071` + cierre formal de hardening y regresiÃ³n |

---


---

# CHECKPOINT MAESTRO â€” INICIO FASE 20

Checkpoint de continuidad creado despuÃ©s del cierre formal de Fase 19.

## Estado consolidado del proyecto

- FASE 01 â€” Fundamentos â€” COMPLETADA
- FASE 02 â€” API / CRUD inicial â€” COMPLETADA
- FASE 03 â€” PostgreSQL â€” COMPLETADA
- FASE 04 â€” Modelado de catÃ¡logo â€” COMPLETADA
- FASE 05 â€” Productos / recetas â€” COMPLETADA
- FASE 06 â€” Locations / disponibilidad â€” COMPLETADA
- FASE 07 â€” Modificaciones â€” COMPLETADA
- FASE 08 â€” Agent / Intent / conversaciÃ³n â€” COMPLETADA
- FASE 09 â€” Ordering integration â€” COMPLETADA
- FASE 10 â€” Precio final â€” COMPLETADA
- FASE 11 â€” Disponibilidad real â€” COMPLETADA
- FASE 12 â€” Consulta de pedidos â€” COMPLETADA
- FASE 13 â€” WhatsApp + Agent + Toast + Dashboard base funcional â€” COMPLETADA
- FASE 14 â€” Pruebas integrales â€” COMPLETADA
- FASE 15 â€” AutenticaciÃ³n y seguridad â€” COMPLETADA
- FASE 16 â€” Datos / migraciones de producciÃ³n â€” COMPLETADA
- FASE 17 â€” Docker / despliegue â€” COMPLETADA
- FASE 18 â€” Staging â€” COMPLETADA
- FASE 19 â€” Integraciones externas â€” COMPLETADA
- FASE 20 â€” Observabilidad, operaciÃ³n y dashboard operativo â€” ACTUAL
- FASE 21 â€” ProducciÃ³n â€” PENDIENTE
- FASE 22 â€” DocumentaciÃ³n / entrega â€” PENDIENTE

## Cierre tÃ©cnico confirmado de Fase 19

Checkpoint documental:

`f8cc731` â€” `docs: close phase 19 and start phase 20`

Checkpoint tÃ©cnico anterior:

`835f071` â€” `harden ambiguous Toast payment recovery`

Validaciones acumuladas al cierre:

- Suite global confirmada: 611 pruebas aprobadas.
- Alembic: `310d4d26a1d6 (head)`.
- Toast Orders integrado.
- Toast Payments integrado.
- Toast Webhooks integrado.
- Fulfillment / KDS integrado.
- Reintentos seguros e idempotencia endurecidos.
- RecuperaciÃ³n de fallos ambiguos de pagos implementada.
- PrevenciÃ³n de duplicados concurrentes implementada.
- External mappings endurecidos contra carreras.
- Aislamiento multi-tenant validado.
- Validaciones E2E de integraciÃ³n completadas.
- Working tree limpio al cierre.
- Rama sincronizada con `origin/feature/orderdb-tenant`.

## Punto exacto de reanudaciÃ³n

La siguiente implementaciÃ³n comienza en:

**FASE 20 â€” Observabilidad, operaciÃ³n y dashboard operativo**

No reconstruir fases 01â€“19 salvo que una regresiÃ³n demuestre un defecto real.

No reabrir Toast Orders, Payments, Webhooks, Fulfillment/KDS,
idempotencia, mappings o aislamiento multi-tenant sin evidencia tÃ©cnica.

## Estado encontrado al iniciar Fase 20

AuditorÃ­a inicial:

- No se detectÃ³ infraestructura propia de logging estructurado en `app`.
- No se detectÃ³ infraestructura propia de mÃ©tricas en `app`.
- No se detectaron health/readiness/liveness routes en `app`.
- Existe dashboard Next.js funcional.
- Dashboard usa Next.js 16.3.4.
- Dashboard usa React 19.2.8.
- Dashboard tiene Playwright.
- Existen pruebas E2E de dashboard para canales, pedidos y estados.

## Plan de ejecuciÃ³n de Fase 20

### 20.1 â€” Observability foundation

Implementar:

- logging estructurado;
- request/correlation IDs;
- tenant context en eventos operativos;
- clasificaciÃ³n consistente de errores;
- eventos operativos relevantes;
- protecciÃ³n contra exposiciÃ³n de secretos o datos sensibles.

### 20.2 â€” Health / readiness / liveness

Implementar:

- health check de API;
- readiness de base de datos;
- liveness;
- estado de dependencias crÃ­ticas cuando corresponda;
- respuestas aptas para infraestructura y monitoreo.

### 20.3 â€” MÃ©tricas operativas

Medir como mÃ­nimo:

- Ã³rdenes;
- Ã³rdenes exitosas/fallidas;
- pagos;
- pagos exitosos/fallidos;
- Toast submissions;
- WhatsApp processing;
- webhooks;
- retries;
- reconciliaciones;
- latencias;
- errores por integraciÃ³n y tenant.

### 20.4 â€” Alertas e incidentes

Definir condiciones operativas para:

- errores repetidos;
- integraciÃ³n caÃ­da;
- fallos de pagos;
- Ã³rdenes atascadas;
- reconciliaciones pendientes;
- webhooks fallidos;
- degradaciÃ³n de servicios.

### 20.5 â€” Operational data layer

Crear servicios/endpoints necesarios para que el dashboard consuma
informaciÃ³n operativa real sin acoplarse directamente a detalles internos
de proveedores externos.

## CHECKPOINT - CIERRE 20.5 OPERATIONAL DATA LAYER

Estado: **COMPLETADA / CERRADA**

Implementado:

- persistencia PostgreSQL de incidentes operativos;
- migración Alembic `e5374cc233ec`;
- servicio persistente de incidentes;
- integración monitor -> almacenamiento persistente;
- worker/runtime automático del monitor operacional;
- API multi-tenant de incidentes para dashboard;
- aislamiento por tenant en métricas, fingerprints e incidentes;
- prevención de re-disparo de incidentes por series métricas no relacionadas;
- identidad persistente estable de `incident_id` en upserts por fingerprint;
- permisos de lectura mediante `VIEW_DASHBOARD`.

Validación final:

- Suite global: **712 passed**.
- Alembic current: `e5374cc233ec (head)`.
- Alembic heads: `e5374cc233ec (head)`.
- `git diff --check`: sin errores.
- Hardening técnico respaldado en commit:
  `d8aa066d3603b7c14daddc94a737ac96c3906193`.

Punto exacto de reanudación:

**20.6 - Arquitectura final del dashboard**

No reabrir 20.5 salvo que una regresión demuestre un defecto real.

---
### 20.6 â€” Arquitectura final del dashboard

Definir y construir:

- navegaciÃ³n;
- layout;
- responsive behavior;
- jerarquÃ­a de informaciÃ³n;
- estados loading / empty / error;
- permisos y visibilidad por rol/tenant.

### 20.7 â€” OperaciÃ³n desde dashboard

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

### 20.8 â€” MÃ©tricas de negocio

Incluir como mÃ­nimo:

- ventas;
- volumen de Ã³rdenes;
- ticket promedio;
- evoluciÃ³n temporal;
- performance por restaurante/location;
- estados y conversiones operativas disponibles.

### 20.9 â€” AdministraciÃ³n

Incluir:

- configuraciÃ³n del restaurante;
- locations;
- usuarios;
- roles/permisos;
- integraciones;
- estado de configuraciÃ³n.

### 20.10 â€” FinalizaciÃ³n y regresiÃ³n de Fase 20

Completar:

- diseÃ±o visual final;
- responsive;
- accesibilidad bÃ¡sica;
- manejo de errores;
- pruebas backend;
- pruebas frontend;
- pruebas E2E;
- regresiÃ³n integral;
- checkpoint final antes de Fase 21.

## Disciplina de trabajo para Fase 20

Cada subfase debe seguir:

1. Inspeccionar primero el cÃ³digo existente.
2. No duplicar funcionalidades ya implementadas.
3. Implementar el bloque completo.
4. Ejecutar pruebas especÃ­ficas.
5. Ejecutar regresiÃ³n relacionada.
6. Revisar `git diff --check`.
7. Confirmar `git status`.
8. Hacer commit descriptivo.
9. Hacer push a `feature/orderdb-tenant`.
10. Confirmar SHA remoto.
11. Actualizar ROADMAP solamente cuando cambie el estado real del proyecto.

No declarar una subfase completada si las pruebas correspondientes no han sido ejecutadas satisfactoriamente.

No crear subfases adicionales sin evidencia tÃ©cnica.

---
# DISCIPLINA DE CHECKPOINTS Y CONTINUIDAD

Desde este checkpoint, **guardar el trabajo** significa sincronizar cÃ³digo y memoria tÃ©cnica del proyecto.

En cada cierre de bloque significativo:

1. Ejecutar las pruebas correspondientes.
2. Confirmar `git status`.
3. Actualizar este ROADMAP si cambiÃ³ fase, subfase, alcance, checkpoint o punto de continuidad.
4. Crear commit del cÃ³digo/documentaciÃ³n.
5. Hacer push a `feature/orderdb-tenant`.
6. Confirmar el SHA remoto.
7. Registrar el siguiente punto exacto de trabajo cuando exista un cambio material.

El historial Git es la evidencia tÃ©cnica y este ROADMAP es el Ã­ndice de continuidad. Ambos deben permanecer alineados.

---

# REGLA DE CONTINUIDAD

Antes de comenzar cualquier nueva fase se debe revisar este archivo y el estado actual de Git.

Antes de cerrar una fase se debe:

1. Ejecutar las pruebas correspondientes.

2. Revisar los cambios de cÃ³digo.

3. Actualizar este `ROADMAP.md`.

4. Crear un commit de checkpoint.

5. Hacer `git push` sobre la rama de trabajo correspondiente y verificar que el checkpoint quede respaldado en GitHub.

6. Verificar que el working tree quede limpio.

El siguiente trabajo comienza siempre desde el Ãºltimo checkpoint confirmado en este documento y en GitHub.