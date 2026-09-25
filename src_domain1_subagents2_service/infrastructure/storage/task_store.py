"""
Task Store implementations
Patrón: Repository Pattern
"""
from typing import Dict, Any, Optional


class InMemoryTaskStore:
    """
    Implementación en memoria del task store
    
    Patrón: Repository - Abstrae el almacenamiento de datos
    Principio: Single Responsibility - Solo maneja persistencia de tareas
    """
    
    def __init__(self):
        self._tasks: Dict[str, Dict[str, Any]] = {}
    
    async def create_task(self, task_id: str, data: Dict[str, Any]) -> None:
        """Crea una nueva tarea"""
        self._tasks[task_id] = data
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene una tarea por ID"""
        return self._tasks.get(task_id)
    
    async def update_task(self, task_id: str, data: Dict[str, Any]) -> None:
        """Actualiza una tarea existente"""
        if task_id in self._tasks:
            self._tasks[task_id].update(data)
    
    async def delete_task(self, task_id: str) -> bool:
        """Elimina una tarea"""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False