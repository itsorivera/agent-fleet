"""Paquete principal del gateway multi-agente A2A (sub-agents).

Layout
    ports/        contratos puros (ChatBackend, A2ASpec, LLMProviderPort)
    adapter/llm/  proveedores de LLM (IAFoundry, AWS Bedrock) tras LLMProviderPort
    utils/        logger (structlog) + backends de chat + wire helpers
    a2a_interface/  recetas de agentes + adapter del a2a-sdk

Entrypoints: `python -m src_domain1_subagents_service.server` (desde la raíz).
"""