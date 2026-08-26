# Fase 13 — Contrato funcional del agente IA

## Objetivo

Definir las reglas que debe seguir el agente conversacional antes de conectar un modelo LLM y WhatsApp.

## 1. Idioma

- El agente responde en el idioma del cliente.
- El agente debe detectar automáticamente el idioma mediante el contexto conversacional y el LLM, sin limitarse a una lista fija de idiomas.
- Si el cliente cambia de idioma, el agente cambia con él.
- El requisito aplica también a idiomas como español, inglés, portugués, francés, mandarín y otros idiomas soportados por el modelo.
- Si el idioma no puede determinarse con suficiente confianza, el agente debe pedir una aclaración natural antes de continuar.
- El idioma de conversación no modifica los datos internos del catálogo.
- Los nombres oficiales de productos e ingredientes deben conservarse cuando sea necesario para evitar ambigüedad.

## 2. Fuente de verdad

El modelo IA no inventa datos de negocio.

- Productos: `search_products_tool`.
- Recetas: `get_product_recipe_tool`.
- Disponibilidad de producto: `check_product_availability_tool`.
- Disponibilidad de ingrediente: `check_ingredient_availability_tool`.
- Modificaciones: `validate_modification_tool`.
- Sedes: `get_location_tool`.
- Precio interno: `calculate_item_price_tool`.

Las reglas de negocio permanecen en los servicios LPDB.

## 3. Recetas

Cuando el cliente pregunte qué ingredientes contiene un producto, el agente debe usar la receta comercial real.

No debe presentar ingredientes de la categoría `EMPAQUE / OPERACIÓN` como ingredientes del producto.

## 4. Modificaciones

El agente no decide si una modificación está permitida.

Debe consultar `validate_modification_tool` y comunicar el resultado al cliente en su idioma.

## 5. Disponibilidad

Antes de confirmar un producto o modificación que dependa de disponibilidad, el agente debe consultar las Tools correspondientes para la sede seleccionada.

No debe prometer disponibilidad sin una respuesta del backend.

## 6. Precios

El precio interno lo calcula LPDB.

El agente puede mostrar un preview interno cuando corresponda, pero no debe presentarlo como el importe final del checkout de Toast.

Toast será la autoridad del cobro final, incluyendo sus cargos, impuestos y propina cuando aplique.

## 7. Confirmación antes de crear una orden

El agente debe separar:

1. Construcción del pedido.
2. Confirmación explícita del cliente.
3. Creación de la orden.

Nunca debe crear una orden únicamente porque el mensaje del cliente parece implicar intención de compra.

Antes de crearla debe presentar un resumen suficientemente claro y pedir confirmación explícita.

## 8. Creación de orden

`create_order` será una operación protegida y no forma parte de la primera tanda de Tools expuestas al LLM.

Cuando se habilite, solo podrá ejecutarse después de confirmación explícita y con sede, productos, cantidades y modificaciones validadas.

## 9. Toast

La integración con Toast se realizará después de estabilizar el agente y sus Tools.

Flujo objetivo:

`WhatsApp → agente IA → LPDB → confirmación → creación de orden → Toast → checkout/pago → operación/cocina`

No se debe asumir todavía el mecanismo exacto de envío a cocina hasta implementar y verificar la integración real con Toast.

## 10. Errores y límites

- Si una Tool falla, el agente debe comunicar una respuesta útil sin inventar un resultado.
- Si falta información necesaria, debe preguntar únicamente por lo necesario.
- Si hay varias sedes posibles, debe pedir al cliente que seleccione una antes de operaciones dependientes de sede.
- El agente debe mantener el contexto de la conversación sin convertir texto libre en datos de negocio no validados.

## Estado

- Tools de consulta y validación: implementadas y probadas localmente.
- Contrato funcional del agente: definido.
- Soporte multidioma: requisito definido.
- LLM: pendiente.
- WhatsApp: pendiente.
- Toast: pendiente.
- Dashboard operativo: pendiente.
