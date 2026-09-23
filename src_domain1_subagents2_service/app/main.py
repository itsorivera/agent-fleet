"""
FastAPI application entry point
"""
from fastapi import FastAPI
from app.api.routes import router as api_router
#from app.middleware.logging import setup_logging
from infrastructure.a2a.server import mount_a2a_agents
from config.settings import get_settings


def create_app() -> FastAPI:
    """
    Factory pattern para crear la aplicación FastAPI
    
    Principios aplicados:
    - Factory Pattern: Centraliza la creación de la app
    - Dependency Injection: Los componentes se inyectan
    - Composite Pattern: Múltiples agentes A2A montados
    """
    app = FastAPI(
        title="A2A Agent Platform",
        description="Multi-agent system with A2A protocol",
        version="1.0.0"
    )
    
    # Setup middleware
    #setup_logging(app)
    
    # Register REST API routes
    app.include_router(api_router, prefix="/api/v1")
    
    # Mount A2A agents (cada agente en su propia URL)
    settings = get_settings()
    if settings.a2a_enabled:
        mount_a2a_agents(app)
        print("🔌 A2A Protocol enabled - Multiple agents mounted")
    
    return app


# Standard FastAPI app
app = create_app()