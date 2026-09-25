"""
A2A Agent Executors - Adaptadores para cada agente
Patrón: Adapter + Factory

Migrados a a2a-sdk 1.1.x: `execute` publica el ciclo de vida de la Task con
los helpers del SDK (new_task_from_user_message + TaskUpdater), no dicts
ad-hoc. La continuidad de un chat va por context_id (en v1.0 las tasks son
inmutables).
"""
from typing import Dict, Type
from a2a.helpers import (
    get_message_text,
    new_task_from_user_message,
    new_text_message,
    new_text_part,
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState

from app.dependencies import get_agent_service


class BaseA2AExecutor(AgentExecutor):
    """
    Executor base para agentes A2A

    Patrón: Template Method + Adapter
    - Adapta nuestro AgentService al protocolo A2A
    - Define el flujo común de ejecución
    """

    # Subclases deben definir el tipo de agente
    agent_type: str = None

    def __init__(self):
        if self.agent_type is None:
            raise ValueError("Subclasses must define agent_type")
        self.agent_service = get_agent_service()

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        """
        Ejecuta agente en contexto A2A

        Patrón: Template Method
        1. Crea (o reutiliza) la Task vigente
        2. Estado working via TaskUpdater
        3. Ejecuta el agente específico (AgentService)
        4. Publica el resultado como artifact y cierra con completed
        """
        # 1. La task del contexto (si el cliente mando un taskId vigente) o una nueva.
        if context.current_task:
            task = context.current_task
        else:
            task = new_task_from_user_message(context.message)
            await event_queue.enqueue_event(task)

        # 2. Estado working.
        updater = TaskUpdater(
            event_queue=event_queue, task_id=task.id, context_id=task.context_id
        )
        await updater.update_status(
            state=TaskState.TASK_STATE_WORKING,
            message=new_text_message("Processing request..."),
        )

        # 3. Ejecuta el agente de aplicación (LangChain / service layer).
        try:
            result = await self.agent_service.execute_agent(
                agent_type=self.agent_type,
                input_data=self._extract_input(context),
                config=self._get_config(context),
            )
            output = self._format_result(result)
        except Exception as e:
            await updater.update_status(
                state=TaskState.TASK_STATE_FAILED,
                message=new_text_message(str(e)),
            )
            raise

        # 4. Artifact con la respuesta y cierre completed.
        await updater.add_artifact(
            parts=[new_text_part(text=output, media_type="text/plain")]
        )
        await updater.update_status(
            state=TaskState.TASK_STATE_COMPLETED,
            message=new_text_message("Request is completed!"),
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        """Cancela ejecución"""
        raise NotImplementedError("Cancel is not supported.")

    def _format_result(self, result: Dict) -> str:
        """Serializa el dict del AgentService a texto plano (artifact A2A)."""
        payload = result.get("result", result)
        if isinstance(payload, dict):
            return str(payload.get("output", payload))
        return str(payload)

    def _extract_input(self, context: RequestContext) -> str:
        """
        Extrae input del contexto A2A

        Hook para personalización por subclases
        """
        return context.get_user_input() if context.message else ""

    def _get_config(self, context: RequestContext) -> Dict:
        """
        Extrae configuración del contexto

        Hook para personalización
        """
        # El LangChain executor lee el tipo de agente de config: lo inyectamos
        # aqui para que cada subclase ejecute su propio agente de aplicacion.
        return {"agent_type": self.agent_type}


class RiskTriageA2AExecutor(BaseA2AExecutor):
    """
    Executor A2A para el agente de triage de riesgo
    
    Patrón: Strategy - Estrategia específica para risk_triage
    """
    agent_type = "risk_triage"


class FraudDetectionA2AExecutor(BaseA2AExecutor):
    """
    Executor A2A para el agente de detección de fraude
    
    Patrón: Strategy - Estrategia específica para fraud_detection
    """
    agent_type = "fraud_detection"


class A2AExecutorFactory:
    """
    Factory para crear executors A2A
    
    Patrón: Factory + Registry
    - Mapea agent_type a su Executor específico
    """
    
    def __init__(self):
        self._executors: Dict[str, Type[BaseA2AExecutor]] = {
            "risk_triage": RiskTriageA2AExecutor,
            "fraud_detection": FraudDetectionA2AExecutor,
        }
    
    def create_executor(self, agent_type: str) -> BaseA2AExecutor:
        """
        Crea un executor para el tipo de agente
        
        Args:
            agent_type: Tipo de agente (debe coincidir con AgentFactory)
            
        Returns:
            Instancia del executor A2A
        """
        executor_class = self._executors.get(agent_type)
        if not executor_class:
            raise ValueError(
                f"No A2A executor found for agent_type: {agent_type}. "
                f"Available: {list(self._executors.keys())}"
            )
        return executor_class()
    
    def register_executor(self, agent_type: str, executor_class: Type[BaseA2AExecutor]):
        """
        Registra un nuevo executor
        
        Patrón: Registry - Extensión dinámica
        """
        self._executors[agent_type] = executor_class
    
    def list_executors(self) -> list:
        """Lista los executors disponibles"""
        return list(self._executors.keys())