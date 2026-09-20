# Agent Fleet — Multi-Agent System on A2A

> This portfolio project exists to demonstrate an **Advanced Agent Paradigm: Supervisor Agent and Sub-agents Architecture**.

A real working **multi-agent system** that communicates over the **A2A protocol** (Agent2Agent, JSON-RPC over HTTP). A **supervisor agent** (orchestrator) maintains the conversation, decides intent, discovers specialist **sub-agents** through a registry of A2A Agent Cards, dispatches the user's message over the wire using the official A2A Python SDK, and returns the sub-agent's response verbatim.

> This is a portfolio project: the point is to show a working, standards-based **supervisor / sub-agents** architecture — not a mock. Run it locally, watch every A2A message in the logs, and reuse the pattern for real services.

---

## What it demonstrates

- **Supervisor Agent and Sub-agents Architecture**: the orchestrator acts as a supervisor — it receives the user request, extracts intent, routes it to the right specialist sub-agent, and streams back the result. Sub-agents are autonomous, discoverable and replaceable.
- **Real A2A dispatch** (v1.0, JSON-RPC over HTTP): the orchestrator resolves an `Agent Card` from `/.well-known/agent-card.json` and sends a `SendMessage` request. No simulated network calls.
- **Orchestrator → sub-agents** workflow (`topic extraction → registry lookup → A2A dispatch`) built with **LangGraph**, with a Google ADK variant included.
- **Multi-agent gateway** exposing multiple sub-agents (`conversational`, `portfolio-qa`) behind a single FastAPI service, each with its own Agent Card, skill and security scheme.
- **Edge auth per agent**: `portfolio-qa` requires `X-API-Key`; the orchestration client injects it via an A2A `ClientCallInterceptor`.
- **Cross-language evidence**: the same A2A Agent interface implemented in **Python (FastAPI)** and **TypeScript (Express)**.
- **Hexagonal architecture**: pure ports (`ChatBackend`, `AgentSpec`), swappable adapters (echo / OpenAI / LiteLLM), and transport-agnostic agent recipes.

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        User (CLI / client)                             │
└───────────────────────────────┬────────────────────────────────────────┘
                                │
                    ┌───────────▼───────────────┐
                    │   SUPERVISOR AGENT         │   src-agent-orchestrator
                    │      (ORCHESTRATOR)        │
                    │    (LangGraph workflow)    │
                    │                            │
                    │ 1. extract primary topic   │  (Gemini 2.5 Flash, or
                    │ 2. search Agent Registry   │   deterministic fallback)
                    │ 3. dispatch via A2A        │
                    └───────────────┬────────────┘
                                    │  A2A: GET /.well-known/agent-card.json
                                    │       POST SendMessage (JSON-RPC 2.0)
                                    ▼
                    ┌───────────────────────────────┐
                    │   A2A MULTI-AGENT GATEWAY     │   src-domain1-agents-service
                    │         (FastAPI)             │
                    │                               │
                    │  ┌───────────────┐  ┌───────────────┐
                    │  │ conversational│  │ portfolio-qa  │  SUB-AGENTS
                    │  │   (public)    │  │ (X-API-Key)   │
                    │  └───────────────┘  └───────────────┘
                    └───────────────────────────────┘
```

### Orchestration flow

```
User Query → [topic_extractor] → [registry_finder] → [a2a_dispatcher] → Output
```

1. **_topic_extractor_** — extracts the single primary topic from the user's message.
2. **_registry_finder_** — searches the local Agent Registry (a catalog of Agent Cards) and picks the matching sub-agent.
3. **_a2a_dispatcher_** — resolves the sub-agent's Agent Card, sends the **original** user message over A2A, and returns the sub-agent's response verbatim.

The dispatcher leaves the message untouched — every comma, name and side-request is forwarded character-for-character, exactly as a semantics-preserving A2A hand-off should.

---

## Repository layout

```
agent-quality
├── src-agent-orchestrator/
│   ├── agent-orchestrator-agnostic.py   # WORKING orchestrator (LangGraph) — real A2A dispatch
│   └── agent-orchestrator.py            # Google ADK (SequentialAgent) variant
├── src-domain1-agents-service/          # A2A multi-agent gateway (FastAPI, hex architecture)
│   ├── app.py                           # composition root: mounts cards + JSON-RPC routes, edge auth
│   ├── server.py                        # uvicorn entrypoint
│   ├── ports/                           # pure ports: ChatBackend (LLM contract), AgentSpec
│   ├── utils/                           # adapters: OpenAI/echo backends, protocol wire helpers
│   └── a2a_interface/                   # agent recipes + a2a-sdk adapter (Template Method)
│       └── agents/                      # one module per agent: sdk_agent, portfolio_qa_agent
├── typescript/                          # same A2A agent interface, TypeScript/Express
├── deploy/                              # Docker Compose: agent + LiteLLM sidecar
├── docs/sidecar-pattern.md              # LLM sidecar architecture decision record
├── .env.example                         # documented configuration
└── pyproject.toml                       # Python deps (uv)
```

---

## Quick start

### 1. Start the A2A multi-agent gateway

```bash
cd src-domain1-agents-service
# Optional: protect the portfolio-qa agent
export PORTFOLIO_QA_API_KEY="dev-key"
python -m server          # → http://127.0.0.1:8080  (port from .env, default 2024)
```

Verify the Agent Cards:

```bash
curl http://127.0.0.1:8080/a2a/conversational/.well-known/agent-card.json
curl http://127.0.0.1:8080/a2a/portfolio-qa/.well-known/agent-card.json
```

### 2. Run the orchestrator

```bash
cd src-agent-orchestrator
export PORTFOLIO_QA_API_KEY="dev-key"        # same key the gateway enforces
python agent-orchestrator-agnostic.py "cuanto vale mi portafolio?"
```

Without a Gemini key, the topic extractor falls back to a **deterministic local matcher** — the demo is fully offline. Set `GOOGLE_API_KEY`/`GEMINI_API_KEY` to use Gemini 2.5 Flash instead.

---

## Verified end-to-end run

```
$ python agent-orchestrator-agnostic.py "cuanto vale mi portafolio?"
============================================================
Orchestrator request: cuanto vale mi portafolio?
Agent service base URL: http://127.0.0.1:8080
============================================================
  [topic_extractor] -> Extracted topic: 'portafolio'
  [registry_finder] -> Found agent: Portfolio QA Agent (domain1/portfolio-qa) @ http://127.0.0.1:8080/a2a/portfolio-qa
  [a2a_dispatcher] -> Sending original message via A2A to http://127.0.0.1:8080/a2a/portfolio-qa
============================================================
FINAL RESPONSE (from sub-agent via A2A):
============================================================
Portfolio QA Agent: El valor actual del portafolio virtual es 125,400 USD. Dispones de 5 posiciones. Puedo darte el detalle por activo.
```

The gateway log shows the real A2A wire traffic — discovery + dispatch:

```
GET  /a2a/portfolio-qa/.well-known/agent-card.json   200 OK
POST /a2a/portfolio-qa                                200 OK
```

---

## The sub-agents

| Agent | Route | Auth | Behaviour |
|---|---|---|---|
| `conversational` | `/a2a/conversational` | public | Generic chat. Backend is pluggable (`echo` for dev, OpenAI for prod). |
| `portfolio-qa` | `/a2a/portfolio-qa` | `X-API-Key` | Read-only Q&A about a virtual portfolio; deterministic rules backend (no tokens burned). |

Both agents are built from the same `AgentRecipe` template — a sub-agent is just *identity + skill + backend*. Adding a new one means adding one module under `a2a_interface/agents/`.

All agents are provider-agnostic: they talk to the `ChatBackend` port. Available adapters: `echo` (zero cost, deterministic), OpenAI-compatible clients, and a **LiteLLM sidecar** for multi-provider failover (see `deploy/` and `docs/sidecar-pattern.md`).

---

## Design highlights

- **A2A by the book**: Agent Card discovery (`/.well-known/agent-card.json`), JSON-RPC 2.0 transport, `SendMessage` with task lifecycle, security schemes declared on the card and enforced at the edge.
- **One agent = one file**: agents are short recipes (`agent_id`, name, skill, backend, security) over a shared Template Method — no duplicated wiring.
- **Hexagonal core**: `ports/` has no infrastructure; `utils/`, `a2a_interface/` and `app.py` are the adapters. This is why the same system can serve `echo`, OpenAI, LiteLLM and the A2A protocol without touching domain logic.
- **Security as a cross-cutting concern**: API keys are validated by HTTP middleware keyed by path prefix; the card only *declares* the scheme.
- **Supervisor / sub-agents decoupled**: the supervisor knows nothing about implementation — only registry entries + A2A. Sub-agents can be replaced, scaled or moved to another host without touching the workflow.

---

## Tech stack

- **Python 3.11**, `a2a-sdk[http-server]` 1.1.x, FastAPI, uvicorn
- **LangGraph** (workflow) with `langchain_core`
- **Google ADK** (alternate orchestrator variant)
- **Gemini 2.5 Flash** (optional topic extraction) / OpenAI / LiteLLM
- **TypeScript / Express** (cross-language A2A agent)
- **Docker Compose + LiteLLM** for the LLM sidecar pattern

---

## Possible next steps

- Replace the local Agent Registry with the **Google Cloud Agent Registry** for managed discovery (the ADK orchestrator is already scaffolded for it).
- Add streaming responses (`message/stream`) in the dispatcher.
- Containerize the orchestrator and wire it into `deploy/compose.yaml`.
- Add multi-turn conversation continuity via A2A `contextId`.

---

## Author

Itsorivera — portfolio project demonstrating the **Supervisor Agent and Sub-agents Architecture** via standards-based, multi-agent interoperability with the A2A protocol.