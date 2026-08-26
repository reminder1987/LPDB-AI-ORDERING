# Fase 13.1 — Auditoría y preparación del Agente IA

## Estado

**EN CURSO**

Este documento complementa `docs/ROADMAP.md` y registra el punto exacto desde el cual continúa la Fase 13.

## Visión del producto

El cliente final utilizará **WhatsApp como canal principal**. No se plantea una app móvil nativa para el cliente.

Flujo objetivo:

```text
CLIENTE
   ↓
WHATSAPP
   ↓
AGENTE IA
   ↓
LPDB CORE
   ├── catálogo
   ├── disponibilidad
   ├── modificaciones
   ├── precios
   └── órdenes
   ↓
CONFIRMACIÓN
   ↓
TOAST
   ↓
PAGO
   ↓
TOAST / KDS
   ↓
COCINA
```

El **dashboard web** será principalmente para el restaurante/administrador.

## Lo que ya existe

### `app/api/agent.py`

Existe `POST /agent/message`, que recibe `session_id`, `customer_name` y `message` y delega en `conversation_service`.

### `app/services/intent_service.py`

Actualmente existe un parser determinístico que interpreta, entre otros:

- productos;
- cantidades;
- `ADD`;
- `REMOVE`;
- `BASE_CHANGE`;
- combos;
- bebidas.

### `app/services/conversation_service.py`

Existe persistencia del estado conversacional en PostgreSQL mediante `ConversationSessionDB`.

El flujo contempla estados conversacionales como:

- pedido nuevo;
- espera de confirmación de combo;
- espera de bebida;
- espera de sede;
- pedido listo.

## Decisión arquitectónica

**No reemplazar el backend de ordering por un LLM.**

La separación objetivo es:

```text
LLM / AGENTE IA
       │
       │ lenguaje natural + contexto + conversación
       ▼
TOOL / SERVICE LAYER
       │
       ├── catálogo
       ├── disponibilidad
       ├── modificaciones
       ├── precios
       └── órdenes
       ▼
LPDB CORE
```

El LLM puede decidir qué necesita entender o consultar, pero las reglas críticas permanecen en el backend.

El agente **no debe inventar**:

- productos;
- precios;
- disponibilidad;
- modificaciones válidas;
- sedes;
- totales.

## Auditoría pendiente

Revisar completamente y clasificar cada servicio:

| Componente | Clasificación |
|---|---|
| `intent_service.py` | 🟡 Requiere adaptación/evaluación para coexistir con LLM |
| `conversation_service.py` | 🟢 Núcleo reutilizable; requiere adaptación al agente final |
| `product_service.py` | ⏳ Auditar |
| `availability_service.py` | ⏳ Auditar |
| `modification_service.py` | ⏳ Auditar |
| `modification_rules.py` | ⏳ Auditar |
| `price_service.py` | ⏳ Auditar |
| `recipe_service.py` | ⏳ Auditar |
| `order_service.py` | ⏳ Auditar |

## Próximo trabajo

1. Auditar los servicios anteriores contra el código real de `master`.
2. Identificar qué funciones pueden exponerse directamente como tools.
3. Identificar qué funciones necesitan wrappers/adaptadores.
4. Definir contratos de entrada/salida de cada tool.
5. Definir cómo el agente mantiene contexto.
6. Definir manejo de errores y validaciones.
7. Definir estrategia de confirmación del pedido.
8. Definir dónde entra el LLM sin duplicar reglas de negocio.
9. Solo después seleccionar/implementar la integración concreta del modelo IA.

## No hacer todavía

- No construir un frontend de cliente móvil.
- No duplicar reglas de negocio en el frontend.
- No sustituir `order_service` por lógica dentro del LLM.
- No asumir proveedor de WhatsApp.
- No asumir permisos o capacidades definitivas de Toast.
- No implementar una pasarela de pago propia.

## Criterio de cierre 13.1

La subfase queda cerrada cuando exista un diseño técnico verificable del agente con:

1. modelo IA definido;
2. contexto definido;
3. tools definidas;
4. contratos de tools definidos;
5. separación IA ↔ reglas de negocio;
6. manejo de errores;
7. estrategia de confirmación;
8. pruebas del flujo agente → tools → LPDB.

## Regla de continuidad

Este documento y `docs/ROADMAP.md` deben revisarse antes de continuar Fase 13. El siguiente trabajo concreto es **terminar la auditoría del código existente**, no empezar todavía a programar WhatsApp o un dashboard sin haber cerrado la arquitectura del agente.
