from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI

from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.types import AgentCard

AGENT_CARD_WELL_KNOWN = "/.well-known/agent.json"


@dataclass
class AgentSpec:
    """Especificación simple de un agente A2A."""
    agent_id: str
    card: AgentCard
    handler: Any  # RequestHandler

    @property
    def rpc_path(self) -> str:
        return f"/a2a/{self.agent_id}"

    @property
    def card_path(self) -> str:
        return f"/a2a/{self.agent_id}/.well-known/agent.json"


def mount_a2a_endpoints(app: Any, spec: AgentSpec, *, root: bool = False) -> None:
    """Monta card + JSON-RPC de un agente en la app."""
    rpc_path = "/" if root else spec.rpc_path
    card_path = AGENT_CARD_WELL_KNOWN if root else spec.card_path

    # Reescribe la URL en la card para que apunte al path real
    if spec.card.supported_interfaces:
        base_url = spec.card.supported_interfaces[0].url
        if base_url:
            spec.card.supported_interfaces[0].url = f"{base_url.rstrip('/')}{rpc_path}"

    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=create_agent_card_routes(spec.card, card_url=card_path),
        jsonrpc_routes=create_jsonrpc_routes(
            spec.handler, rpc_path, enable_v0_3_compat=True
        ),
    )


def create_app(agents: list[AgentSpec] | None = None) -> FastAPI:
    """Ensambla el gateway multi-agente A2A."""
    load_dotenv(override=True)

    app = FastAPI(title="A2A multi-agent gateway", version="0.1.0")

    app.state.a2a: dict[str, object] = {}
    for spec in agents or []:
        mount_a2a_endpoints(app, spec)
        app.state.a2a[spec.agent_id] = spec.handler

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "agents": [a.agent_id for a in (agents or [])]}

    return app