"""Backends de chat interpolables (adapters del puerto ChatBackend).

Los contratos (``ChatBackend``/``ChatBackendBase``) viven en
src/ports/llm.py; aqui estan las implementaciones concretas: OpenAI,
Azure Foundry via APIM, echo, mas los mappers y la factory. La capa A2A
(server.py) nunca sabe si detras hay OpenAI, un LLM local o un echo fijo:
solo conoce el puerto.

Para verificar el protocolo sin gastar tokens, usa `provider="echo"`
(CHAT_PROVIDER=echo). Produccion: "openai" contra cualquier compatible, o
"azure" para consumir un modelo de Azure Foundry a traves del AI Gateway
(APIM) — governance/monitoreo del LLM en el punto central.
"""

from __future__ import annotations

import os
from typing import Any, AsyncIterator, Dict, List

from src_domain1_subagents1_service.utils.protocol import parts_to_text
from src_domain1_subagents1_service.ports.llm import ChatBackend, ChatBackendBase


def history_to_openai(history: List[Dict[str, Any]], system: str) -> List[Dict[str, str]]:
    """Convierte history A2A (role user/agent + parts) al formato chat de OpenAI.

    Nota: aqui es donde se "puentea" el modelo de mensajes A2A al modelo de
    mensajes del proveedor. Es la misma traduccion que hace LangGraph entre
    su estado `messages` y el wire format A2A (pero transparente).
    """
    messages: List[Dict[str, str]] = [{"role": "system", "content": system}]
    for m in history:
        content = parts_to_text(m.get("parts", []))
        if not content:
            continue
        role = "user" if m.get("role") == "user" else "assistant"
        messages.append({"role": role, "content": content})
    return messages


class OpenAIBackend(ChatBackendBase):
    """Backend real usando el cliente oficial de OpenAI (async, con streaming).

    Override del Template Method: aqui el streaming es real (trozo por trozo
    desde la API), no una simulacion de caracteres.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        base_url: str | None = None,
    ):
        from openai import AsyncOpenAI

        base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._temperature = temperature

    async def chat(self, *, system: str, history: List[Dict[str, Any]]) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=history_to_openai(history, system),
            temperature=self._temperature,
        )
        return response.choices[0].message.content or ""

    def stream(self, *, system: str, history: List[Dict[str, Any]]) -> AsyncIterator[str]:
        return self._stream(system, history)

    async def _stream(self, system: str, history: List[Dict[str, Any]]) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=history_to_openai(history, system),
            temperature=self._temperature,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta


class EchoBackend(ChatBackendBase):
    """Backend de prueba: devuelve un echo del ultimo mensaje.

    Muy util para (1) verificar el protocolo sin API key y (2) demostrar la
    interoperabilidad Python<->TypeScript con un costo determinista.
    """

    def __init__(self, prefix: str = "Agent"):
        self._prefix = prefix

    def _last_text(self, history: List[Dict[str, Any]]) -> str:
        return parts_to_text(history[-1].get("parts", [])) if history else ""

    async def chat(self, *, system: str, history: List[Dict[str, Any]]) -> str:
        return f"{self._prefix} echo: {self._last_text(history)}"


class AzureChatBackend(ChatBackendBase):
    """Backend hacia modelos de Azure Foundry a traves del AI Gateway (APIM).

    Envuelve ``AzureChatOpenAI`` (langchain-openai) apuntando al endpoint de
    APIM en vez de directo al deployment de Foundry. Todo el trafico del LLM
    pasa por un unico choke point donde el gateway aplica gobierno de uso
    (quota, RBAC), monitoreo (telemetria de tokens/costo por flota) y control
    (routing/failover). La identidad del agente viaja en headers propios:
    ``X-Agent-Fleet`` y ``X-Business-Unit``, ademas de la subscription key.

    El ``deployment`` debe coincidir con el nombre desplegado en Foundry.
    """

    def __init__(
        self,
        *,
        endpoint: str,
        deployment: str,
        api_version: str,
        api_key: str,
        temperature: float | None = None,
        fleet: str = "fleet-lab-01",
        business_unit: str = "sandbox",
    ):
        from src_domain1_subagents1_service.adapter.llm.ia_foundry_provider_llm_adapter import (
            IAFoundryLLMAdapter,
        )

        # El agente nunca construye clientes directamente: delega la creacion
        # del AzureChatOpenAI en el patron maduro LLMProviderPort (IAFoundry).
        # Quien quiera otro proveedor solo cambia el adapter del puerto.
        adapter = IAFoundryLLMAdapter(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            deployment_name=deployment,
            fleet=fleet,
            business_unit=business_unit,
        )
        self._chat = adapter.get_llm(model_id=deployment, temperature=temperature)

    @staticmethod
    def _content_text(content: Any) -> str:
        """Normaliza `content` de LangChain (str | list de bloques) a texto."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: List[str] = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict) and block.get("type") == "text":
                    parts.append(str(block.get("text", "")))
            return "".join(parts)
        return str(content)

    def _messages(self, system: str, history: List[Dict[str, Any]]):
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        messages = [SystemMessage(content=system)]
        for m in history:
            content = parts_to_text(m.get("parts", []))
            if not content:
                continue
            role = "user" if m.get("role") == "user" else "assistant"
            messages.append(HumanMessage(content=content) if role == "user" else AIMessage(content=content))
        return messages

    async def chat(self, *, system: str, history: List[Dict[str, Any]]) -> str:
        response = await self._chat.ainvoke(self._messages(system, history))
        return self._content_text(response.content)

    async def _stream(self, system: str, history: List[Dict[str, Any]]) -> AsyncIterator[str]:
        async for chunk in self._chat.astream(self._messages(system, history)):
            text = self._content_text(chunk.content)
            if text:
                yield text


def build_backend(
    provider: str = "openai",
    *,
    api_key: str | None = None,
    model: str = "gpt-4o-mini",
    agent_name: str = "Agent",
) -> ChatBackend:
    """Factory que elige backend segun configuracion (env CHAT_PROVIDER)."""
    if provider == "echo":
        return EchoBackend(prefix=agent_name)
    if provider == "azure":
        key = os.getenv("AZ_APIM_SUBSCRIPTION_KEY") or api_key
        endpoint = os.getenv("AZ_AI_ENDPOINT")
        if not (key and endpoint):
            raise RuntimeError(
                "provider=azure requiere AZ_APIM_SUBSCRIPTION_KEY y AZ_AI_ENDPOINT (o usa CHAT_PROVIDER=echo para pruebas)"
            )
        deployment = (
            os.getenv("AZ_DEPLOYMENT") or os.getenv("AZURE_DEPLOYMENT") or model
        )
        return AzureChatBackend(
            endpoint=endpoint,
            deployment=deployment,
            api_version=os.getenv("AZURE_API_VERSION", "2024-10-21"),
            api_key=key,
        )
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "provider=openai requiere OPENAI_API_KEY (o usa CHAT_PROVIDER=echo para pruebas)"
        )
    return OpenAIBackend(api_key=key, model=model)