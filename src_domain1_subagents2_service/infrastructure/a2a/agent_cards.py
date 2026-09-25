"""
A2A Agent Cards - Metadata de agentes según estándar A2A
Patrón: Registry + Factory
"""
from typing import Dict
from a2a.types import AgentCard, AgentSkill, AgentCapabilities, AgentInterface


class AgentCardRegistry:
    """
    Registry de AgentCards para múltiples agentes
    
    Patrón: Registry
    - Cada agente tiene su propia AgentCard
    - Permite descubrimiento dinámico de agentes
    """
    
    def __init__(self, base_url: str = "https://agents.example.com"):
        self.base_url = base_url
        self._cards: Dict[str, AgentCard] = {}
        self._register_default_cards()
    
    def _register_default_cards(self):
        """Registra las AgentCards por defecto"""
        self.register_card("risk_triage", self._create_risk_triage_card())
        self.register_card("fraud_detection", self._create_fraud_detection_card())
    
    def _create_risk_triage_card(self) -> AgentCard:
        """
        AgentCard para el agente de triage de riesgo
        
        Según estándar A2A, define:
        - Capacidades (streaming, notificaciones)
        - Skills (qué puede hacer)
        - Interfaces (cómo comunicarse)
        """
        return AgentCard(
            name="Risk Triage Agent",
            version="1.0.0",
            description="Agente especializado en triage y clasificación de alertas de riesgo",
            capabilities=AgentCapabilities(
                streaming=True,
                push_notifications=True
            ),
            skills=[
                AgentSkill(
                    id="risk-triage",
                    name="Risk Triage",
                    description="Analiza y clasifica alertas de riesgo por severidad y prioridad",
                    tags=["risk", "triage", "security", "classification"],
                    input_modes=["application/json", "text/plain"],
                    output_modes=["application/json"]
                )
            ],
            supported_interfaces=[
                AgentInterface(
                    protocol_binding="JSONRPC",
                    url=f"{self.base_url}/a2a/risk-triage",  # URL específica
                    protocol_version="1.0"
                )
            ]
        )
    
    def _create_fraud_detection_card(self) -> AgentCard:
        """
        AgentCard para el agente de detección de fraude
        
        Cada agente tiene su propia card con URL única
        """
        return AgentCard(
            name="Fraud Detection Agent",
            version="1.0.0",
            description="Agente especializado en detección y prevención de fraude financiero",
            capabilities=AgentCapabilities(
                streaming=True,
                push_notifications=True
            ),
            skills=[
                AgentSkill(
                    id="fraud-detection",
                    name="Fraud Detection",
                    description="Detecta patrones de fraude en transacciones financieras",
                    tags=["fraud", "detection", "financial", "security"],
                    input_modes=["application/json", "text/plain"],
                    output_modes=["application/json"]
                )
            ],
            supported_interfaces=[
                AgentInterface(
                    protocol_binding="JSONRPC",
                    url=f"{self.base_url}/a2a/fraud-detection",  # URL única
                    protocol_version="1.0"
                )
            ]
        )
    
    def register_card(self, agent_type: str, card: AgentCard):
        """
        Registra una nueva AgentCard
        
        Patrón: Registry - Permite extensión dinámica
        """
        self._cards[agent_type] = card
    
    def get_card(self, agent_type: str) -> AgentCard:
        """Obtiene la AgentCard de un agente"""
        card = self._cards.get(agent_type)
        if not card:
            raise ValueError(
                f"No AgentCard found for agent_type: {agent_type}. "
                f"Available: {list(self._cards.keys())}"
            )
        return card
    
    def list_cards(self) -> Dict[str, AgentCard]:
        """Lista todas las AgentCards disponibles"""
        return self._cards.copy()