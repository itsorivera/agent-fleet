"""
Base Agent - Template Method Pattern
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncIterator


class BaseAgent(ABC):
    """
    Clase base para todos los agentes
    
    Patrón: Template Method
    - Define el esqueleto del algoritmo
    - Las subclases implementan pasos específicos
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._setup()
    
    def _setup(self):
        """Hook para inicialización específica"""
        pass
    
    @abstractmethod
    async def _process(self, input_data: str) -> str:
        """
        Lógica específica del agente
        
        Template Method: Cada agente implementa su lógica
        """
        pass
    
    async def run(self, input_data: str) -> str:
        """
        Template method - Define el flujo general
        
        Patrón: Template Method
        1. Pre-procesamiento
        2. Procesamiento (implementado por subclases)
        3. Post-procesamiento
        """
        # Pre-procesamiento
        processed_input = await self._preprocess(input_data)
        
        # Procesamiento principal (delegado a subclases)
        result = await self._process(processed_input)
        
        # Post-procesamiento
        final_result = await self._postprocess(result)
        
        return final_result
    
    async def _preprocess(self, input_data: str) -> str:
        """Hook para pre-procesamiento"""
        return input_data.strip()
    
    async def _postprocess(self, result: str) -> str:
        """Hook para post-procesamiento"""
        return result
    
    async def stream(self, input_data: str) -> AsyncIterator[str]:
        """
        Streaming execution
        
        Por defecto, retorna el resultado completo
        Las subclases pueden override para streaming real
        """
        result = await self.run(input_data)
        yield result