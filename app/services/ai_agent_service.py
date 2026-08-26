"""
Servicio base del agente IA.

Esta primera versión establece la frontera entre la conversación y el
proveedor LLM. No crea órdenes y no ejecuta acciones de negocio por sí sola.
"""

from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class AgentResponse:
    message: str
    language: str


class AIAgentService:
    """
    Punto único de entrada para el agente conversacional.

    La integración concreta con el proveedor LLM se añadirá después de
    validar esta frontera. Mantenerla aislada evita acoplar FastAPI,
    WhatsApp y las reglas de negocio al SDK del proveedor.
    """

    def __init__(self) -> None:
        self.model = settings.openai_model

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

        spanish_score = sum(marker in f" {text} " for marker in spanish_markers)
        english_score = sum(marker in f" {text} " for marker in english_markers)

        if spanish_score > english_score:
            return "es"
        if english_score > spanish_score:
            return "en"
        return "unknown"

    def build_system_instructions(self, language: str) -> str:
        """Construye las reglas base que deberá recibir el LLM."""
        response_language = {
            "es": "Responde en español.",
            "en": "Respond in English.",
            "unknown": (
                "Responde en el idioma del cliente y conserva el idioma "
                "de la conversación cuando sea posible."
            ),
        }.get(language, "Responde en el idioma del cliente.")

        return "\n".join(
            [
                "Eres el asistente de pedidos de Los Perritos Del Barrio.",
                response_language,
                "No inventes productos, recetas, disponibilidad ni precios.",
                "Usa las herramientas de LPDB para consultar datos de negocio.",
                "No presentes ingredientes de EMPAQUE / OPERACIÓN como ingredientes del producto.",
                "No crees una orden sin confirmación explícita del cliente.",
                "El precio interno de LPDB no es el cobro final de Toast.",
                "No inventes cargos, impuestos ni propina de Toast.",
            ]
        )

    def prepare_request(self, message: str) -> dict:
        """Prepara el contexto mínimo para una futura llamada al LLM."""
        language = self.detect_language(message)
        return {
            "model": self.model,
            "language": language,
            "system_instructions": self.build_system_instructions(language),
            "message": message,
        }


ai_agent_service = AIAgentService()
