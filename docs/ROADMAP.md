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

**Fase actual:** 13 — Canal de cliente, agente IA y dashboard operativo  
**Estado:** EN DEFINICIÓN / PRÓXIMA IMPLEMENTACIÓN  
**Última fase completada:** 12 — Consulta de pedidos  
**Último checkpoint:** `221116b` — `feat: completar consultas de pedidos fase 12`  
**Rama principal:** `master`

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

# FASE 13 — Canal de cliente, agente IA y dashboard operativo

**Estado:** EN DEFINICIÓN / PRÓXIMA IMPLEMENTACIÓN

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
              │  AGENTE DE IA   │
              │    WHATSAPP     │
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
**Estado:** PENDIENTE

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
- Seguridad de webhooks y callbacks.

## FASE 16 — Datos y migraciones de producción
**Estado:** PENDIENTE

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
**Estado:** PENDIENTE

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
**Estado:** PENDIENTE

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
**Estado:** PENDIENTE

### Alcance

Integraciones externas necesarias para el producto final:

- WhatsApp.
- Toast Orders API.
- Toast Payments, según capacidades y autorización del restaurante.
- Toast webhooks.
- Toast/KDS y fulfillment.
- Otras integraciones que sean necesarias.

### Principio arquitectónico

```text
LPDB-AI-ORDERING
        ↓
Integration Layer
        ↓
Servicios externos
```

Las integraciones externas no deben contaminar el núcleo de ordering.

### Criterio de cierre

Las integraciones definidas para producción deben funcionar con autenticación, manejo de errores, mapeo de datos, estados, reintentos cuando corresponda y pruebas.

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
- Seguimiento de webhooks, pagos y sincronización con POS.

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
FASE 01 — Fundamentos del proyecto                    ✅
FASE 02 — API / CRUD inicial                          ✅
FASE 03 — PostgreSQL                                  ✅
FASE 04 — Modelado de catálogo                       ✅
FASE 05 — Productos / recetas                        ✅
FASE 06 — Sedes / disponibilidad                     ✅
FASE 07 — Modificaciones                              ✅
FASE 08 — Agent / Intent / conversación               ✅
FASE 09 — Integración completa ordering               ✅
FASE 10 — Precio final                                ✅
FASE 11 — Disponibilidad real                         ✅
FASE 12 — Consulta de pedidos                         ✅
FASE 13 — WhatsApp + Agent + Toast + Dashboard        ▶️ ACTUAL
FASE 14 — Pruebas integrales                          ⏳
FASE 15 — Autenticación y seguridad                    ⏳
FASE 16 — Datos / migraciones producción              ⏳
FASE 17 — Docker / despliegue                         ⏳
FASE 18 — Staging                                     ⏳
FASE 19 — Integraciones externas                      ⏳
FASE 20 — Observabilidad                              ⏳
FASE 21 — Producción                                  ⏳
FASE 22 — Documentación / entrega                     ⏳
```

---

# CHECKPOINTS

| Fase | Estado | Checkpoint |
|---|---|---|
| 10 | COMPLETADA | Integrada en el estado funcional previo |
| 11 | COMPLETADA | Integrada en el estado funcional previo |
| 12 | COMPLETADA | `221116b` |
| 13 | EN DEFINICIÓN / PRÓXIMA IMPLEMENTACIÓN | Pendiente |

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
