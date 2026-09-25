"""
Agent Executor Interface
Patrón: Interface Segregation Principle (ISP)
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncIterator


class AgentExecutorInterface(ABC):
    """
    Contrato para ejecutores de agentes
    
    Principio SOLID: Interface Segregation
    - Define el contrato mínimo que debe cumplir cualquier executor
    """
    
    @abstractmethod
    async def execute(
        self, 
        input_data: str, 
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta el agente con los datos de entrada
        
        Args:
            input_data: Datos de entrada para el agente
            config: Configuración adicional
            
        Returns:
            Resultado de la ejecución
        """
        pass
    
    @abstractmethod
    async def stream_execute(
        self, 
        input_data: str, 
        config: Dict[str, Any] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Ejecuta el agente con streaming de resultados
        
        Patrón: Iterator pattern para streaming
        """
        pass
    
    @abstractmethod
    async def cancel(self, task_id: str) -> bool:
        """Cancela una ejecución en progreso"""
        pass