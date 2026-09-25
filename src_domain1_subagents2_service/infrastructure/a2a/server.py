"""
A2A Server Integration - Multi-Agent Support
Patrón: Adapter + Registry - Soporta múltiples agentes A2A

Migrado a a2a-sdk 1.1.x: en vez del helper `A2AFastAPIApplication` (eliminado
en 1.1.0), cada agente registra sus rutas directamente en la app principal
con las funciones de `a2a.server.routes` (add_a2a_routes_to_fastapi +
create_jsonrpc_routes + create_agent_card_routes), cada uno en
`/a2a/<agent-type-dashed>` con paths exactos, su propia AgentCard y su propio
DefaultRequestHandler compartiendo un InMemoryTaskStore (mismo patrón que
src_domain1_subagents1_service).
"""
from typing import Dict, List
from fastapi import FastAPI

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
)

from infrastructure.a2a.agent_cards import AgentCardRegistry
from infrastructure.a2a.executors import A2AExecutorFactory
from config.settings import get_settings


class A2AMultiAgentServer:
    """
    Servidor A2A multi-agente

    Patrón: Facade + Registry
    - Gestiona múltiples agentes A2A
    - Cada agente tiene su propia AgentCard, Executor y URL
    """

    def __init__(self, base_url: str = None):
        settings = get_settings()
        self.base_url = base_url or settings.a2a_base_url

        # Registries
        self.card_registry = AgentCardRegistry(base_url=self.base_url)
        self.executor_factory = A2AExecutorFactory()

        # Task store compartido
        self.task_store = InMemoryTaskStore()

    def _build_handler(self, agent_type: str, card) -> DefaultRequestHandler:
        """Crea el handler A2A (executor propio + task store compartido).

        Patrón: Factory
        - Cada agente tiene su propio AgentExecutor (y su AgentCard).
        - El DefaultRequestHandler 1.1.x exige la card y el task store.
        """
        executor = self.executor_factory.create_executor(agent_type)
        return DefaultRequestHandler(
            agent_executor=executor,
            task_store=self.task_store,
            agent_card=card,
        )

    def agent_route(self, agent_type: str) -> str:
        """Path RPC del agente en el gateway (card y rutas usan el mismo)."""
        return f"/a2a/{agent_type.replace('_', '-')}"

    def register_agent_routes(self, main_app: FastAPI) -> None:
        """Registra las rutas A2A de cada agente en la app principal.

        Se registran con paths exactos en la app principal (sin mounts):
        los mounts de Starlette redirigen `/a2a/risk-triage` -> `/a2a/.../`
        (307), y la card anuncia la URL sin slash; este es el mismo patron
        que usa src_domain1_subagents1_service.
        """
        for agent_type, card in self.card_registry.list_cards().items():
            rpc_path = self.agent_route(agent_type)
            card_path = f"{rpc_path}/.well-known/agent-card.json"
            handler = self._build_handler(agent_type, card)

            add_a2a_routes_to_fastapi(
                main_app,
                agent_card_routes=create_agent_card_routes(card, card_url=card_path),
                jsonrpc_routes=create_jsonrpc_routes(
                    handler, rpc_url=rpc_path, enable_v0_3_compat=True
                ),
            )
            print(f"[OK] A2A Agent mounted: {rpc_path}")

    def register_new_agent(self, agent_type: str, card, executor_class):
        """
        Registra un nuevo agente dinámicamente

        Patrón: Registry - Extensión en runtime
        """
        self.card_registry.register_card(agent_type, card)
        self.executor_factory.register_executor(agent_type, executor_class)

    def list_agents(self) -> List[str]:
        """Lista todos los agentes A2A disponibles"""
        return list(self.card_registry.list_cards().keys())


def mount_a2a_agents(main_app: FastAPI) -> FastAPI:
    """
    Registra todos los agentes A2A en la aplicación principal

    Patrón: Composite
    - Cada agente se registra en su propia ruta con paths exactos
    - /a2a/risk-triage -> RiskTriageAgent
    - /a2a/fraud-detection -> FraudDetectionAgent

    Args:
        main_app: Aplicación FastAPI principal

    Returns:
        FastAPI app con agentes A2A montados
    """
    server = A2AMultiAgentServer()
    server.register_agent_routes(main_app)
    return main_app


def create_a2a_server() -> A2AMultiAgentServer:
    """
    Factory para crear el servidor A2A multi-agente

    Patrón: Factory
    """
    return A2AMultiAgentServer()