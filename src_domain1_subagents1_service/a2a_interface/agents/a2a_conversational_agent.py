"""Agente conversacional (``agent_id="conversational"``): receta + factory.

Cada agente vive en su propio modulo (patron "un agente = un archivo"). Este
solo declara el delta de su receta sobre A2AAgentRecipe (a2a_protocol.a2a_recipe):
identidad, system prompt y skill. Todo el cableado (card + handler + adapter)
lo resuelve A2AAgentRecipe.build() -> produce un A2ASpec listo para montar.

Sin transporte: no importa FastAPI/uvicorn. El composition root (app.py) y
el entrypoint (server.py) deciden la exposicion.
"""

from __future__ import annotations

import os

from a2a.types import AgentSkill

from src_domain1_subagents1_service.utils.llm import build_backend
from src_domain1_subagents1_service.a2a_interface.a2a_recipe import (
    A2AAgentRecipe,
    A2AAgentConfig,
)
from src_domain1_subagents1_service.ports.llm import ChatBackend
from src_domain1_subagents1_service.ports.spec import A2ASpec


class A2AConversationalAgent(A2AAgentRecipe):
    """Receta del agente conversacional: su unico delta respecto a la base.

    Identidad, backend y skill; todo el cableado (card + handler + adapter)
    lo resuelve A2AAgentRecipe.build().
    """

    agent_id = "conversational"

    def __init__(
        self,
        *,
        settings: A2AAgentConfig,
        backend: ChatBackend,
        name: str,
        description: str,
    ):
        super().__init__(settings=settings, backend=backend)
        self._name = name
        self._description = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def build_system_prompt(self) -> str:
        return os.getenv("SYSTEM_PROMPT") or f"You are {self.name}. {self.description}"

    def build_skills(self) -> list[AgentSkill]:
        return [
            AgentSkill(
                id="conversation",
                name="Conversational Chat",
                description="Participates in text conversations via the A2A protocol (SDK implementation).",
                tags=["chat", "conversation", "sdk"],
                examples=["Hello", "What can you help me with?"],
            )
        ]


def build_conversational_agent(
    settings: A2AAgentConfig | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
) -> A2ASpec:
    """Factory inyectable del agente conversacional.

    Si pasas ``settings``/``name``/``description`` explicitos, el unico
    entorno que aun lee es el del backend (CHAT_PROVIDER/OPENAI_*), con el
    fallback dev ``echo``. Para inyeccion estricta, server.py construye el
    ``ChatBackend`` y pasa el resto por parametro.
    """
    settings = settings or A2AAgentConfig.from_env()
    name = name or os.getenv("AGENT_NAME", "SDK Conversational Agent")
    description = description or os.getenv(
        "AGENT_DESCRIPTION", "A conversational agent exposed over A2A via the official SDK."
    )
    backend = build_backend(
        os.getenv("CHAT_PROVIDER", "echo"),
        api_key=os.getenv("AZ_APIM_SUBSCRIPTION_KEY"),
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        agent_name=name,
    )
    return A2AConversationalAgent(
        settings=settings, backend=backend, name=name, description=description
    ).build()