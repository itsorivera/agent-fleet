"""
Agent Service - Orquesta la ejecución de agentes
Patrón: Service Layer + Facade
"""
import uuid
from typing import Dict, Any, Optional

from core.interfaces.agent_executor import AgentExecutorInterface


class AgentService:
    """
    Servicio de aplicación para gestión de agentes
    
    Patrones aplicados:
    - Service Layer: Encapsula lógica de negocio
    - Facade: Simplifica interacción con subsistemas
    - Dependency Injection: Recibe dependencias por constructor
    """
    
    def __init__(
        self, 
        executor: AgentExecutorInterface,
        task_store: Any  # Podría ser una interfaz también
    ):
        self.executor = executor
        self.task_store = task_store
    
    async def execute_agent(
        self,
        agent_type: str,
        input_data: str,
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta un agente y gestiona el ciclo de vida de la tarea
        
        Responsabilidad única: Orquestar la ejecución
        """
        task_id = str(uuid.uuid4())
        
        # Guardar tarea en store
        await self.task_store.create_task(task_id, {
            "agent_type": agent_type,
            "status": "running",
            "input": input_data
        })
        
        try:
            # Ejecutar agente
            result = await self.executor.execute(
                input_data=input_data,
                config=config or {}
            )
            
            # Actualizar estado
            await self.task_store.update_task(task_id, {
                "status": "completed",
                "result": result
            })
            
            return {
                "task_id": task_id,
                "result": result
            }
            
        except Exception as e:
            # Manejo de errores
            await self.task_store.update_task(task_id, {
                "status": "failed",
                "error": str(e)
            })
            raise
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el estado de una tarea"""
        return await self.task_store.get_task(task_id)