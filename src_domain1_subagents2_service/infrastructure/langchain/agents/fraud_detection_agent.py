"""
Fraud Detection Agent - Implementación específica
Patrón: Strategy - Nueva estrategia de procesamiento
"""
from typing import AsyncIterator
from infrastructure.langchain.agents.base import BaseAgent


class FraudDetectionAgent(BaseAgent):
    """
    Agente especializado en detección de fraude
    
    Ejemplo de cómo agregar un nuevo agente sin modificar código existente
    Principio: Open/Closed - Abierto a extensión
    """
    
    def _setup(self):
        """Inicialización específica del agente de fraude"""
        self.model = self.config.get("model", "gpt-4")
        self.temperature = self.config.get("temperature", 0.3)  # Más determinista
        self.threshold = self.config.get("fraud_threshold", 0.7)
        
        # En producción:
        # self.llm = ChatOpenAI(model=self.model, temperature=self.temperature)
        # self.embeddings = OpenAIEmbeddings()
    
    async def _process(self, input_data: str) -> str:
        """
        Lógica de detección de fraude
        
        En producción usarías:
        - LangChain's ChatOpenAI
        - Vector stores para patrones de fraude
        - Chains con memoria
        """
        prompt = self._build_fraud_prompt(input_data)
        
        # Simulación - En producción usarías LangChain real
        result = f"""
        🔍 ANÁLISIS DE FRAUDE:
        Transacción analizada: {input_data}
        
        ⚠️ Nivel de Riesgo: ALTO
        📊 Score de Fraude: 0.85/1.00
        🎯 Confianza: 92%
        
        🚨 Indicadores detectados:
        - Patrón de gasto inusual (+350% vs promedio)
        - Ubicación geográfica sospechosa
        - Horario atípico de transacción
        - Monto superior al límite habitual
        
        💡 Recomendación: BLOQUEAR y solicitar verificación adicional
        📞 Acción sugerida: Contactar al cliente inmediatamente
        """
        
        return result.strip()
    
    def _build_fraud_prompt(self, input_data: str) -> str:
        """
        Construye el prompt especializado para fraude
        
        Patrón: Builder - Construcción de prompts complejos
        """
        return f"""
        Eres un experto en detección de fraude financiero con 20 años de experiencia.
        Analiza la siguiente transacción en busca de patrones sospechosos:
        
        {input_data}
        
        Evalúa:
        1. Patrones de comportamiento anómalos
        2. Indicadores de riesgo geográfico
        3. Análisis de monto y frecuencia
        4. Correlación con fraudes conocidos
        
        Proporciona un score de 0 a 1 y recomendaciones de acción.
        """
    
    async def stream(self, input_data: str) -> AsyncIterator[str]:
        """
        Streaming para análisis en tiempo real
        """
        # Simula análisis progresivo
        steps = [
            "🔍 Iniciando análisis de fraude...",
            "📊 Evaluando patrones de comportamiento...",
            "🌍 Verificando ubicación geográfica...",
            "💰 Analizando monto y frecuencia...",
        ]
        
        for step in steps:
            yield step + "\n"
        
        # Resultado final
        result = await self._process(input_data)
        yield "\n" + result