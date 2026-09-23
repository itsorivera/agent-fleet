"""
API Routes - REST endpoints para interactuar con agentes
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from app.dependencies import get_agent_service
from core.services.agent_service import AgentService


router = APIRouter()


class AgentRequest(BaseModel):
    """Request model para ejecutar agente"""
    input: str
    agent_type: str = "risk_triage"
    config: Dict[str, Any] = {}


class AgentResponse(BaseModel):
    """Response model"""
    task_id: str
    status: str
    result: Dict[str, Any] = {}


@router.post("/agents/execute", response_model=AgentResponse)
async def execute_agent(
    request: AgentRequest,
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    Ejecuta un agente de forma asíncrona
    
    Patrón aplicado: Facade - Simplifica la interacción con el sistema de agentes
    """
    try:
        result = await agent_service.execute_agent(
            agent_type=request.agent_type,
            input_data=request.input,
            config=request.config
        )
        return AgentResponse(
            task_id=result.get("task_id", ""),
            status="completed",
            result=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{task_id}/status")
async def get_task_status(
    task_id: str,
    agent_service: AgentService = Depends(get_agent_service)
):
    """Obtiene el estado de una tarea"""
    status = await agent_service.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return status


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "a2a-agent-platform"}


@router.get("/agents/list")
async def list_available_agents():
    """
    Lista todos los agentes disponibles (REST y A2A)
    
    Returns:
        Lista de agentes con sus capacidades y URLs
    """
    from infrastructure.a2a.server import create_a2a_server
    from config.settings import get_settings
    
    settings = get_settings()
    agents = []
    
    # Agentes disponibles vía REST
    agents.append({
        "name": "risk_triage",
        "type": "REST",
        "url": "/api/v1/agents/execute",
        "description": "Risk triage agent via REST API"
    })
    
    agents.append({
        "name": "fraud_detection",
        "type": "REST",
        "url": "/api/v1/agents/execute",
        "description": "Fraud detection agent via REST API"
    })
    
    # Agentes A2A (si está habilitado)
    if settings.a2a_enabled:
        a2a_server = create_a2a_server()
        for agent_type in a2a_server.list_agents():
            agents.append({
                "name": agent_type,
                "type": "A2A",
                "url": f"/a2a/{agent_type.replace('_', '-')}",
                "description": f"{agent_type} agent via A2A protocol"
            })
    
    return {
        "total": len(agents),
        "agents": agents,
        "a2a_enabled": settings.a2a_enabled
    }