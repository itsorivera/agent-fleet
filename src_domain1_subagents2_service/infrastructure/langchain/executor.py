"""
LangChain Agent Executor
Patrón: Adapter - Adapta LangChain al contrato AgentExecutorInterface
"""
from typing import Dict, Any, AsyncIterator
from core.interfaces.agent_executor import AgentExecutorInterface
from infrastructure.langchain.agents.factory import AgentFactory


class LangChainAgentExecutor(AgentExecutorInterface):
    """
    Implementación de AgentExecutor usando LangChain
    
    Patrones:
    - Adapter: Adapta LangChain a nuestra interfaz
    - Strategy: Delega la estrategia de ejecución al agente específico
    """
    
    def __init__(self):
        self.agent_factory = AgentFactory()
    
    async def execute(
        self, 
        input_data: str, 
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta un agente LangChain
        
        Patrón Factory: Usa factory para crear el agente apropiado
        """
        config = config or {}
        agent_type = config.get("agent_type", "risk_triage")
        
        # Factory pattern: Crea el agente según tipo
        agent = self.agent_factory.create_agent(agent_type)
        
        # Ejecuta el agente
        result = await agent.run(input_data)
        
        return {
            "output": result,
            "agent_type": agent_type,
            "metadata": {
                "model": config.get("model", "gpt-4"),
                "temperature": config.get("temperature", 0.7)
            }
        }
    
    async def stream_execute(
        self, 
        input_data: str, 
        config: Dict[str, Any] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Ejecuta con streaming
        
        Patrón: Iterator/Generator para streaming
        """
        config = config or {}
        agent_type = config.get("agent_type", "risk_triage")
        
        agent = self.agent_factory.create_agent(agent_type)
        
        async for chunk in agent.stream(input_data):
            yield {
                "chunk": chunk,
                "agent_type": agent_type
            }
    
    async def cancel(self, task_id: str) -> bool:
        """Cancela ejecución (placeholder)"""
        # Implementación depende de cómo LangChain maneja cancelaciones
        return True