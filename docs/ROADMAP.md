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

**Fase actual:** 13 — Frontend  
**Estado:** EN PROGRESO  
**Última fase completada:** 12 — Consulta de pedidos  
**Último checkpoint:** `221116b` — `feat: completar consultas de pedidos fase 12`  
**Rama principal:** `master`

---

# FASES DEL PROYECTO

## FASE 01 — Fundamentos del proyecto

**Estado:** COMPLETADA

Base inicial del proyecto, estructura, entorno y configuración fundamental.

---

## FASE 02 — API / CRUD inicial

**Estado:** COMPLETADA

Construcción inicial de la API de pedidos y operaciones CRUD.

---

## FASE 03 — PostgreSQL

**Estado:** COMPLETADA

Migración de la persistencia de pedidos hacia PostgreSQL y consolidación del acceso a datos.

---

## FASE 04 — Modelado de catálogo

**Estado:** COMPLETADA

Modelos de productos, categorías e ingredientes y relaciones del catálogo.

---

## FASE 05 — Productos / recetas

**Estado:** COMPLETADA

Catálogo, recetas y estructura necesaria para determinar composición y reglas de productos.

---

## FASE 06 — Sedes / disponibilidad

**Estado:** COMPLETADA

Sedes, disponibilidad de productos e ingredientes y servicios relacionados.

---

## FASE 07 — Modificaciones

**Estado:** COMPLETADA

Reglas y persistencia de modificaciones de pedidos:

- `ADD`
- `REMOVE`
- `BASE_CHANGE`
- Validaciones de modificaciones.

---

## FASE 08 — Agent / Intent / conversación

**Estado:** COMPLETADA

Interpretación de mensajes del cliente, detección de productos, cantidades, modificaciones, combos y flujo conversacional.

---

## FASE 09 — Integración completa de ordering

**Estado:** COMPLETADA

Integración del flujo completo de creación de pedidos con catálogo, modificaciones, disponibilidad, sedes, conversación y persistencia.

---

## FASE 10 — Precio final

**Estado:** COMPLETADA

### Alcance

- Precio base de cada producto.
- Precio de `ADD`.
- `REMOVE` sin costo adicional.
- `BASE_CHANGE` según producto/base resultante.
- Cantidades.
- Múltiples productos.
- Combos y bebida.
- Subtotal y total consistentes en respuesta y BD.
- No inventar precios de combo mientras no estén definidos.

---

## FASE 11 — Disponibilidad real

**Estado:** COMPLETADA

### Alcance

- Producto disponible/no disponible.
- Ingredientes y modificaciones válidas según disponibilidad.
- Bebidas disponibles.
- Validación antes de crear la orden.
- Integración con el flujo conversacional.

---

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
- Combos.
- Bebidas.
- Precio de combo.
- `unit_price`.
- `subtotal`.
- `total`.
- `404` para pedido inexistente.

### Checkpoint

`221116b` — `feat: completar consultas de pedidos fase 12`

---

## FASE 13 — Frontend

**Estado:** EN PROGRESO

### Objetivo

Construir la interfaz web que consuma la API real del proyecto sin duplicar la lógica de negocio del backend.

### Alcance previsto

- Pantalla principal.
- Catálogo de productos.
- Productos disponibles/no disponibles.
- Selección de cantidad.
- Modificaciones `ADD`, `REMOVE` y `BASE_CHANGE`.
- Combos.
- Bebidas.
- Carrito/pedido.
- Precios.
- Subtotal.
- Total.
- Confirmación del pedido.
- Consulta de pedidos.
- Manejo de errores de API.
- Estados de carga.
- Diseño responsive.

### Principio arquitectónico

El frontend presenta y solicita operaciones; la API permanece como fuente de verdad para reglas de negocio, disponibilidad, modificaciones y precios.

```text
FRONTEND
   ↓
FASTAPI
   ↓
SERVICES
   ↓
POSTGRESQL
```

### Criterio de cierre

El flujo principal de ordering debe poder ejecutarse desde la interfaz, consumiendo los endpoints reales y reflejando correctamente productos, cantidades, modificaciones, combos, disponibilidad y precios.

---

## FASE 14 — Pruebas integrales

**Estado:** PENDIENTE

### Alcance

- Pruebas del backend completo.
- Pruebas del frontend.
- Pruebas de integración frontend ↔ API.
- Flujos End-to-End.
- Casos positivos y negativos.
- Regresiones de las Fases 10–13.
- Reducción de dependencia de pruebas manuales.

### Criterio de cierre

Los flujos principales del sistema deben estar cubiertos por pruebas reproducibles y pasar sin regresiones.

---

## FASE 15 — Autenticación y seguridad

**Estado:** PENDIENTE

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

### Criterio de cierre

Los usuarios y operaciones estén protegidos según sus permisos y las credenciales sensibles no formen parte del código ni del repositorio.

---

## FASE 16 — Datos y migraciones de producción

**Estado:** PENDIENTE

### Alcance

- Revisión de migraciones Alembic.
- Seeds y datos iniciales.
- Integridad referencial.
- Constraints.
- Índices necesarios.
- Tratamiento de datos legacy.
- Estrategia de backup.
- Estrategia de restauración.
- Flujo desarrollo → staging → producción.

### Criterio de cierre

La base de datos de producción debe poder crearse y actualizarse mediante migraciones reproducibles sin copiar manualmente la BD de desarrollo.

---

## FASE 17 — Docker y despliegue

**Estado:** PENDIENTE

### Alcance

- Contenerización del backend.
- Configuración de ejecución para producción.
- Variables de entorno.
- Secrets.
- Health checks.
- Configuración de servicios.
- Preparación del frontend para despliegue.

### Criterio de cierre

El sistema debe poder ejecutarse de forma reproducible fuera del entorno local de desarrollo.

---

## FASE 18 — Staging

**Estado:** PENDIENTE

### Alcance

- Entorno de staging.
- Deploy de backend y frontend.
- Base de datos de staging.
- Configuración independiente de producción.
- Pruebas desde Internet.
- Smoke tests.
- Correcciones antes de producción.

### Flujo

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

---

## FASE 19 — Integraciones externas

**Estado:** PENDIENTE

### Alcance

Integraciones externas necesarias para el producto final, incluyendo Toast si forma parte del alcance definitivo.

### Principio arquitectónico

Las integraciones externas deben vivir detrás de una capa de integración y no contaminar el núcleo de ordering.

```text
LPDB-AI-ORDERING
        ↓
Integration Layer
        ↓
Servicios externos
```

### Criterio de cierre

Las integraciones definidas para producción deben funcionar con autenticación, manejo de errores, mapeo de datos y pruebas.

---

## FASE 20 — Observabilidad y operación

**Estado:** PENDIENTE

### Alcance

- Logging.
- Manejo y seguimiento de errores.
- Health checks.
- Métricas.
- Monitoreo.
- Alertas.
- Auditoría.
- Seguimiento de operaciones e integraciones.

### Criterio de cierre

Los problemas relevantes del sistema deben poder detectarse, diagnosticarse y rastrearse en producción.

---

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
- Smoke tests.
- Prueba real de creación y consulta de pedidos.

### Criterio de cierre

La aplicación debe estar disponible públicamente y operar correctamente en un entorno productivo controlado.

---

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
- Frontend.
- Deployment.
- Integraciones.
- Troubleshooting.
- Procedimientos operativos.

### Criterio de cierre

El proyecto debe poder ser instalado, entendido, operado y mantenido por otra persona sin depender de la memoria de esta conversación.

---

# MAPA RESUMIDO

```text
FASE 01 — Fundamentos del proyecto             ✅
FASE 02 — API / CRUD inicial                   ✅
FASE 03 — PostgreSQL                            ✅
FASE 04 — Modelado de catálogo                 ✅
FASE 05 — Productos / recetas                  ✅
FASE 06 — Sedes / disponibilidad               ✅
FASE 07 — Modificaciones                       ✅
FASE 08 — Agent / Intent / conversación        ✅
FASE 09 — Integración completa ordering        ✅
FASE 10 — Precio final                         ✅
FASE 11 — Disponibilidad real                  ✅
FASE 12 — Consulta de pedidos                  ✅
FASE 13 — Frontend                             ▶️ ACTUAL
FASE 14 — Pruebas integrales                   ⏳
FASE 15 — Autenticación y seguridad             ⏳
FASE 16 — Datos / migraciones producción       ⏳
FASE 17 — Docker / despliegue                  ⏳
FASE 18 — Staging                              ⏳
FASE 19 — Integraciones externas               ⏳
FASE 20 — Observabilidad                       ⏳
FASE 21 — Producción                           ⏳
FASE 22 — Documentación / entrega              ⏳
```

---

# CHECKPOINTS

| Fase | Estado | Checkpoint |
|---|---|---|
| 10 | COMPLETADA | Integrada en el estado funcional previo |
| 11 | COMPLETADA | Integrada en el estado funcional previo |
| 12 | COMPLETADA | `221116b` |
| 13 | EN PROGRESO | Pendiente de implementación |

---

# REGLA DE CONTINUIDAD

Antes de comenzar cualquier nueva fase se debe revisar este archivo y el estado actual de Git.

Antes de cerrar una fase se debe:

1. Ejecutar las pruebas correspondientes.
2. Revisar los cambios de código.
3. Actualizar este `ROADMAP.md`.
4. Crear un commit de checkpoint.
5. Hacer `git push origin master`.
6. Verificar que el working tree quede limpio.

El siguiente trabajo comienza siempre desde el último checkpoint confirmado en este documento y en GitHub.
