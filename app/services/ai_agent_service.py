"""
Servicio principal del agente IA.

Este módulo conecta la conversación con OpenAI Responses API y el
registro central de herramientas de LPDB.

Responsabilidades:

- Detectar el idioma básico de la conversación.
- Construir las instrucciones del sistema.
- Enviar el mensaje al LLM.
- Procesar tool calls.
- Ejecutar las tools mediante agent_tool_registry.
- Inyectar TenantContext de forma interna.
- Devolver la respuesta final del agente.

Las reglas de negocio permanecen en los servicios Core.
El LLM no accede directamente a la base de datos.
"""

import json
from dataclasses import dataclass

from openai import OpenAI

from app.core.config import settings
from app.core.tenant_context import TenantContext
from app.services.agent_tool_registry import (
    execute_tool,
    get_tool_definitions,
)


@dataclass(frozen=True)
class AgentResponse:
    message: str
    language: str


class AIAgentService:
    """
    Orquestador principal del agente conversacional.

    OpenAI decide cuándo necesita una herramienta.
    Las herramientas se ejecutan exclusivamente mediante el registry.

    TenantContext nunca es controlado por el modelo.
    """

    def __init__(self) -> None:
        self.model = settings.openai_model

        if not settings.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY no está configurada."
            )

        self.client = OpenAI(
            api_key=settings.openai_api_key,
        )

    def detect_language(self, message: str) -> str:
        """Detecta de forma determinista el idioma básico de una entrada."""
        text = message.lower()

        spanish_markers = (
            " el ",
            " la ",
            " los ",
            " las ",
            " que ",
            " quiero ",
            " tiene ",
            " trae ",
            " pedido ",
        )

        english_markers = (
            " the ",
            " a ",
            " an ",
            " what ",
            " want ",
            " have ",
            " comes ",
            " order ",
        )

        spanish_score = sum(
            marker in f" {text} "
            for marker in spanish_markers
        )

        english_score = sum(
            marker in f" {text} "
            for marker in english_markers
        )

        if spanish_score > english_score:
            return "es"

        if english_score > spanish_score:
            return "en"

        return "unknown"

    def build_system_instructions(
        self,
        language: str,
        tenant_context: TenantContext,
    ) -> str:
        """Construye las instrucciones base que recibe el LLM."""

        response_language = {
            "es": "Responde en español.",
            "en": "Respond in English.",
            "unknown": (
                "Responde en el idioma del cliente y conserva el idioma "
                "de la conversación cuando sea posible."
            ),
        }.get(
            language,
            "Responde en el idioma del cliente.",
        )

        return "\n".join(
            [
                "Eres el asistente de pedidos de Los Perritos Del Barrio.",
                f"Tenant activo: {tenant_context.tenant_name}.",
                response_language,
                "No inventes productos, recetas, disponibilidad ni precios.",
                "Usa las herramientas de LPDB para consultar datos de negocio.",
                (
                    "Todas las consultas y acciones de negocio deben "
                    "respetar el tenant activo."
                ),
                (
                    "No presentes ingredientes de EMPAQUE / OPERACIÓN "
                    "como ingredientes del producto."
                ),
                (
                    "No crees una orden sin confirmación explícita "
                    "del cliente."
                ),
                (
                    "Nunca inventes product_id, ingredient_id o "
                    "location_id. Obtén los IDs mediante las tools."
                ),
                (
                    "El precio interno de LPDB no es el cobro final "
                    "de Toast."
                ),
                "No inventes cargos, impuestos ni propina de Toast.",
                (
                    "Antes de crear una orden, verifica que el cliente "
                    "haya confirmado explícitamente el pedido completo."
                ),
            ]
        )

    def prepare_request(
        self,
        message: str,
        tenant_context: TenantContext,
    ) -> dict:
        """
        Prepara el contexto mínimo para una llamada al LLM.

        Se conserva este método como frontera útil para pruebas y
        compatibilidad con el código existente.
        """

        language = self.detect_language(message)

        return {
            "model": self.model,
            "language": language,
            "tenant_id": tenant_context.tenant_id,
            "tenant_slug": tenant_context.tenant_slug,
            "tenant_name": tenant_context.tenant_name,
            "system_instructions": self.build_system_instructions(
                language,
                tenant_context,
            ),
            "message": message,
        }

    def _serialize_tool_result(
        self,
        result,
    ) -> str:
        """
        Convierte el resultado de una tool a JSON para devolverlo
        al modelo como tool output.
        """

        return json.dumps(
            result,
            ensure_ascii=False,
            default=str,
        )

    def _extract_text(
        self,
        response,
    ) -> str:
        """Extrae el texto final generado por Responses API."""

        output_text = getattr(
            response,
            "output_text",
            None,
        )

        if output_text:
            return output_text

        return ""

    def _get_function_calls(
        self,
        response,
    ) -> list:
        """Obtiene los function calls contenidos en la respuesta."""

        output = getattr(
            response,
            "output",
            [],
        )

        return [
            item
            for item in output
            if getattr(
                item,
                "type",
                None,
            )
            == "function_call"
        ]

    def process_message(
        self,
        message: str,
        tenant_context: TenantContext,
    ) -> AgentResponse:
        """
        Procesa un mensaje mediante OpenAI Responses API.

        El ciclo continúa mientras el modelo solicite herramientas.

        Flujo:

            mensaje
                ↓
            OpenAI
                ↓
            function_call
                ↓
            registry
                ↓
            tool
                ↓
            resultado
                ↓
            OpenAI
                ↓
            respuesta final
        """

        language = self.detect_language(
            message
        )

        instructions = self.build_system_instructions(
            language,
            tenant_context,
        )

        response = self.client.responses.create(
            model=self.model,
            instructions=instructions,
            input=message,
            tools=get_tool_definitions(),
            store=False,
        )

        while True:
            function_calls = self._get_function_calls(
                response
            )

            if not function_calls:
                break

            tool_outputs = []

            for function_call in function_calls:
                tool_name = function_call.name

                try:
                    arguments = json.loads(
                        function_call.arguments
                    )

                except (
                    TypeError,
                    json.JSONDecodeError,
                ) as exc:
                    tool_result = {
                        "ok": False,
                        "error": (
                            "Argumentos inválidos para la tool "
                            f"{tool_name}: {exc}"
                        ),
                    }

                else:
                    try:
                        tool_result = execute_tool(
                            tool_name=tool_name,
                            arguments=arguments,
                            tenant=tenant_context,
                        )

                    except Exception as exc:
                        tool_result = {
                            "ok": False,
                            "error": str(exc),
                        }

                tool_outputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": function_call.call_id,
                        "output": self._serialize_tool_result(
                            tool_result
                        ),
                    }
                )

            response = self.client.responses.create(
                model=self.model,
                instructions=instructions,
                previous_response_id=response.id,
                input=tool_outputs,
                tools=get_tool_definitions(),
                store=False,
            )

        message_text = self._extract_text(
            response
        )

        if not message_text:
            message_text = (
                "No pude generar una respuesta en este momento."
            )

        return AgentResponse(
            message=message_text,
            language=language,
        )


ai_agent_service = AIAgentService()