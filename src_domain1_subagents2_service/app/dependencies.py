"""
Dependency Injection container
Patrón: Dependency Injection + Singleton
"""
from functools import lru_cache

from core.services.agent_service import AgentService
from core.interfaces.agent_executor import AgentExecutorInterface
from infrastructure.langchain.executor import LangChainAgentExecutor
from infrastructure.storage.task_store import InMemoryTaskStore


@lru_cache()
def get_task_store():
    """Singleton task store"""
    return InMemoryTaskStore()


@lru_cache()
def get_agent_executor() -> AgentExecutorInterface:
    """
    Factory para crear el executor de agentes
    
    Principio: Dependency Inversion - Retorna una interfaz, no implementación concreta
    """
    return LangChainAgentExecutor()


@lru_cache()
def get_agent_service() -> AgentService:
    """
    Servicio principal de agentes
    
    Patrón: Service Layer - Encapsula la lógica de negocio
    """
    return AgentService(
        executor=get_agent_executor(),
        task_store=get_task_store()
    )