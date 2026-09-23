#!/usr/bin/env python3
"""
Server Entry Point - Uvicorn ASGI Server
Patrón: Separation of Concerns

Este archivo es el ÚNICO punto de entrada para ejecutar el servidor.
Separa la configuración del servidor (deployment) de la lógica de aplicación.
"""
import uvicorn
#from config.settings import get_settings
#from config.logging_config import setup_logging


def main():
    """
    Punto de entrada principal del servidor
    
    Principio: Single Responsibility
    - Este archivo solo se encarga de EJECUTAR el servidor
    - La configuración de la app está en app/main.py
    - La configuración del entorno está en config/settings.py
    """
    # Setup logging
    #setup_logging()
    
    # Get settings
    #settings = get_settings()
    
    # Configuración de Uvicorn
    uvicorn_config = {
        "app": "app.main:app",  # Import path a la FastAPI app
        "host": settings.host,
        "port": settings.port,
        "reload": settings.debug,  # Hot reload en desarrollo
        "log_level": settings.log_level.lower(),
        "access_log": True,
    }
    
    # En producción, agregar workers
    if not settings.debug:
        uvicorn_config.update({
            "workers": 4,  # Múltiples workers para producción
            "loop": "uvloop",  # Event loop más rápido
            "http": "httptools",  # Parser HTTP más rápido
        })
    
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"📍 Server: http://{settings.host}:{settings.port}")
    print(f"📚 Docs: http://{settings.host}:{settings.port}/docs")
    print(f"🔧 Mode: {'Development' if settings.debug else 'Production'}")
    
    # Ejecutar servidor
    uvicorn.run(**uvicorn_config)


if __name__ == "__main__":
    main()