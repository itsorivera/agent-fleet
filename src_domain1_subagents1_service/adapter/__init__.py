"""Adapters de infraestructura (patrón hexagonal).

Cada adapter resuelve un puerto de `ports/`. `adapter/llm/` implementa
`LLMProviderPort` con proveedores concretos (IAFoundry, AWS Bedrock).
"""