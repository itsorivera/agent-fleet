"""
Agent Factory - Factory Pattern
"""
from typing import Dict, Any
from infrastructure.langchain.agents.base import BaseAgent
from infrastructure.langchain.agents.risk_triage_agent import RiskTriageAgent
from infrastructure.langchain.agents.fraud_detection_agent import FraudDetectionAgent


class AgentFactory:
    """
    Factory para crear agentes
    
    Patrón: Factory Method
    - Centraliza la creación de agentes
    - Permite extensibilidad sin modificar código existente (Open/Closed)
    """
    
    def __init__(self):
        # Registry pattern: Mapeo de tipos a clases
        self._agents = {
            "risk_triage": RiskTriageAgent,
            "fraud_detection": FraudDetectionAgent,  # ✅ Nuevo agente agregado
            # Fácil agregar más agentes:
            # "compliance_check": ComplianceAgent,
        }
    
    def create_agent(
        self, 
        agent_type: str, 
        config: Dict[str, Any] = None
    ) -> BaseAgent:
        """
        Crea un agente según el tipo
        
        Patrón: Factory Method + Registry
        
        Args:
            agent_type: Tipo de agente a crear
            config: Configuración del agente
            
        Returns:
            Instancia del agente
            
        Raises:
            ValueError: Si el tipo de agente no existe
        """
        agent_class = self._agents.get(agent_type)
        
        if not agent_class:
            raise ValueError(
                f"Unknown agent type: {agent_type}. "
                f"Available: {list(self._agents.keys())}"
            )
        
        return agent_class(config=config or {})
    
    def register_agent(self, agent_type: str, agent_class: type):
        """
        Registra un nuevo tipo de agente
        
        Patrón: Registry - Permite extensión dinámica
        Principio: Open/Closed - Abierto a extensión, cerrado a modificación
        """
        self._agents[agent_type] = agent_class
    
    def list_available_agents(self) -> list:
        """Lista los agentes disponibles"""
        return list(self._agents.keys())