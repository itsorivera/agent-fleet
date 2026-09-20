"""
OrchestratorAgent (LangGraph Edition)
Agnostic multi-agent orchestration. Descubre sub-agentes via un registry
local (Agent Cards) y les despacha el mensaje del usuario por el protocolo
A2A real (JSON-RPC sobre HTTP) usando el A2A Python SDK.

Workflow:
  User Query -> extract_topic -> find_in_registry -> dispatch_a2a -> Output

Los sub-agentes que descubre son los expuestos por src-domain1-agents-service
(gateway A2A): "conversational" (publico) y "portfolio-qa" (protegido con
API key X-API-Key). El orquestador resuelve cada Agent Card via
<base_url>/a2a/<agent_id>/.well-known/agent-card.json y envia el mensaje
original caracter por caracter, devolviendo la respuesta del sub-agente
verbatim (patron claro de A2A en un sistema multi-agente).
"""

import asyncio
import os
import sys
import uuid
from typing import Dict, Any, Optional
from typing_extensions import TypedDict
from pathlib import Path
from dotenv import load_dotenv

# Make imports resolvable regardless of CWD (runnable from repo root or dir).
_SRC_DIR = Path(__file__).resolve().parent
for _p in (_SRC_DIR.parent, _SRC_DIR.parent / "src-domain1-agents-service"):
    sys.path.insert(0, str(_p))

load_dotenv(_SRC_DIR.parent / ".env")

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from a2a.client import ClientCallContext, ClientConfig, create_client
from a2a.client.interceptors import BeforeArgs, ClientCallInterceptor
from a2a.helpers import get_stream_response_text


# ===========================================================================
# 1. Registry de sub-agentes (estado: apunta al gateway A2A real)
# ===========================================================================
AGENT_SERVICE_BASE_URL = os.getenv(
    "AGENT_SERVICE_BASE_URL", "http://127.0.0.1:8080"
).rstrip("/")

# El X-API-Key exigido por el agente portfolio-qa (mismo valor con el que se
# levanta el gateway: PORTFOLIO_QA_API_KEY en el .env del service).
PORTFOLIO_QA_API_KEY = os.getenv("PORTFOLIO_QA_API_KEY", "")


def _agent_url(agent_id: str) -> str:
    return f"{AGENT_SERVICE_BASE_URL}/a2a/{agent_id}"


# Cada entrada modela una Agent Card de src-domain1-agents-service. El
# "endpoint" es la URL del agente; el SDK la usa para resolver la card y
# negociar el transporte JSON-RPC real.
LOCAL_AGENT_REGISTRY = [
    {
        "resource_name": "domain1/conversational",
        "name": "SDK Conversational Agent",
        "description": "A conversational agent exposed over A2A via the official SDK.",
        "skills": ["conversational", "chat", "conversation", "sdk"],
        "endpoint": _agent_url("conversational"),
        "requires_api_key": False,
    },
    {
        "resource_name": "domain1/portfolio-qa",
        "name": "Portfolio QA Agent",
        "description": "Read-only assistant that answers questions about the user's virtual portfolio.",
        "skills": [
            "portfolio",
            "qa",
            "valor",
            "capital",
            "portafolio",
            "rentabilidad",
            "activos",
            "riesgo",
        ],
        "endpoint": _agent_url("portfolio-qa"),
        "requires_api_key": True,
    },
]


def search_registry(search_query: str) -> Optional[Dict[str, Any]]:
    """Busqueda lexica/semantica sobre el registry local de Agent Cards.

    Devuelve la primera card cuyo nombre o skills coincide con el topic.
    Fallback: primera card (mismo comportamiento que la instruccion previa).
    """
    normalized_query = search_query.lower()
    for agent in LOCAL_AGENT_REGISTRY:
        if any(skill in normalized_query for skill in agent["skills"]):
            return agent
        if normalized_query in agent["description"].lower():
            return agent
    return LOCAL_AGENT_REGISTRY[0] if LOCAL_AGENT_REGISTRY else None


# ===========================================================================
# 2. Interceptor A2A: inyecta el header X-API-Key cuando el agente lo pide
# ===========================================================================
class ApiKeyInterceptor(ClientCallInterceptor):
    """Adjunta el header de API key (X-API-Key) a las llamadas salientes.

    El gateway de src-domain1-agents-service valida este header en el edge
    para el agente portfolio-qa (ver server.py / app.api_key_gate). Si el
    agente no requiere key, no se anade nada.
    """

    def __init__(self, api_key: str):
        self._api_key = api_key

    async def before(self, args: BeforeArgs) -> None:
        if not self._api_key:
            return
        if args.context is None:
            args.context = ClientCallContext()
        if args.context.service_parameters is None:
            args.context.service_parameters = {}
        args.context.service_parameters["X-API-Key"] = self._api_key

    async def after(self, args: Any) -> None:
        return


async def call_remote_a2a_agent(
    agent_card: Dict[str, Any], message: str
) -> str:
    """Despacha el mensaje al sub-agente remoto por A2A real (JSON-RPC/HTTP).

    Resuelve la Agent Card del endpoint, envia el mensaje original (sin
    modificarlo) y devuelve la respuesta del sub-agente verbatim.
    """
    endpoint = agent_card["endpoint"]

    interceptors: list[ClientCallInterceptor] = []
    if agent_card.get("requires_api_key"):
        interceptors.append(ApiKeyInterceptor(PORTFOLIO_QA_API_KEY))

    # Non-streaming: mensaje/send directo (JSON-RPC), evita SSE y simplifica
    # la integracion. Igualmente es un despacho A2A 1.0 real sobre HTTP.
    client = await create_client(
        endpoint,
        client_config=ClientConfig(streaming=False, polling=False),
        interceptors=interceptors,
    )
    try:
        from a2a.types import Message, Part, Role, SendMessageRequest

        request = SendMessageRequest(
            message=Message(
                role=Role.ROLE_USER,
                message_id=str(uuid.uuid4()),
                parts=[Part(text=message)],
            )
        )
        parts: list[str] = []
        async for response in client.send_message(request):
            text = get_stream_response_text(response)
            if text:
                parts.append(text)
        answer = "\n".join(parts).strip()
        if not answer:
            answer = "(sin respuesta de texto del sub-agente)"
        return answer
    finally:
        await client.close()


# ===========================================================================
# 3. Definicion del Estado de LangGraph
# ===========================================================================
class OrchestratorState(TypedDict):
    original_message: str
    primary_topic: Optional[str]
    agent_card: Optional[Dict[str, Any]]
    final_response: Optional[str]


# ===========================================================================
# 4. Definicion de Nodos de la Arquitectura
# ===========================================================================
# Extraccion de topic. Si hay GOOGLE_API_KEY/GEMINI_API_KEY y el paquete
# langchain_google_genai esta instalado, usa Gemini; si no, cae a un
# extractor determinista por keywords para que la demo corra 100% local
# sin credenciales ni dependencias opcionales.
def _build_llm():
    if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
        return None
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI  # noqa: PLC0415

        return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    except ImportError:
        return None


llm = _build_llm()

TOPIC_INSTRUCTION = """You extract the SINGLE primary topic from the user's message.

Rules:
- Output ONLY the topic phrase on one line — no preamble, no punctuation, no quotes.
- If the user mentions multiple topics, pick ONE: usually the first concrete request,
  or the bigger task. Side requests and afterthoughts are NOT the primary topic.
- Valid examples: "dog walk", "trip planning", "weather report", "portfolio value".
"""


async def _topic_by_llm(message: str) -> str:
    prompt = ChatPromptTemplate.from_messages(
        [("system", TOPIC_INSTRUCTION), ("user", "{input}")]
    )
    chain = prompt | llm
    response = await chain.ainvoke({"input": message})
    return response.content.strip().strip('"').strip("'")


def _topic_by_keywords(message: str) -> str:
    """Fallback determinista: devuelve el first matching skill del registry."""
    low = message.lower()
    for agent in LOCAL_AGENT_REGISTRY:
        for skill in agent["skills"]:
            if skill.lower() in low:
                return skill
    return "portfolio"


async def topic_extractor_node(state: OrchestratorState) -> Dict[str, Any]:
    message = state["original_message"]
    if llm is not None:
        topic = await _topic_by_llm(message)
    else:
        topic = _topic_by_keywords(message)
    print(f"  [topic_extractor] -> Extracted topic: '{topic}'")
    return {"primary_topic": topic}


async def registry_finder_node(state: OrchestratorState) -> Dict[str, Any]:
    topic = state.get("primary_topic", "")
    agent_card = search_registry(topic)
    print(
        f"  [registry_finder] -> Found agent: {agent_card['name']} "
        f"({agent_card['resource_name']}) @ {agent_card['endpoint']}"
    )
    return {"agent_card": agent_card}


async def a2a_dispatcher_node(state: OrchestratorState) -> Dict[str, Any]:
    agent_card = state["agent_card"]
    original_message = state["original_message"]

    if not agent_card:
        return {
            "final_response": "Error: No suitable agent was found in the registry."
        }

    print(
        f"  [a2a_dispatcher] -> Sending original message via A2A to "
        f"{agent_card['endpoint']}"
    )
    response = await call_remote_a2a_agent(agent_card, original_message)
    return {"final_response": response}


# ===========================================================================
# 5. Compilacion del Grafo (LangGraph Workflow)
# ===========================================================================
workflow = StateGraph(OrchestratorState)

workflow.add_node("topic_extractor", topic_extractor_node)
workflow.add_node("registry_finder", registry_finder_node)
workflow.add_node("a2a_dispatcher", a2a_dispatcher_node)

workflow.set_entry_point("topic_extractor")
workflow.add_edge("topic_extractor", "registry_finder")
workflow.add_edge("registry_finder", "a2a_dispatcher")
workflow.add_edge("a2a_dispatcher", END)

orchestrator_graph = workflow.compile()


# ===========================================================================
# 6. Runtime Execution
# ===========================================================================
async def main():
    query = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "How much is my portfolio worth right now?"
    )

    print("=" * 60)
    print(f"Orchestrator request: {query}")
    print(f"Agent service base URL: {AGENT_SERVICE_BASE_URL}")
    print("=" * 60)

    initial_state: OrchestratorState = {
        "original_message": query,
        "primary_topic": None,
        "agent_card": None,
        "final_response": None,
    }

    result = await orchestrator_graph.ainvoke(initial_state)

    print("\n" + "=" * 60)
    print("FINAL RESPONSE (from sub-agent via A2A):")
    print("=" * 60)
    print(result.get("final_response"))
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
