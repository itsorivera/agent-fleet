"""Configuración del servicio leída del entorno (Single Source of Truth).

Patrón: Settings + cached factory (`get_settings`), sin dependencias extra
(más allá de `python-dotenv`, ya en el repo). Los valores por defecto replican
el despliegue de dev del resto del repo; en producción se sobrescriben con env.

Atributos y de dónde sale cada uno (contrato de uso real):
    host / port / debug / log_level   -> server.py (diccionario de Uvicorn)
    a2a_enabled                       -> app/main.py y app/api/routes.py
                                         (montar/desmontar el protocolo A2A)
    a2a_base_url                      -> infrastructure/a2a/server.py
                                         (base de la AgentCard discovery)

Env vars soportadas: HOST, PORT, DEBUG, LOG_LEVEL, A2A_ENABLED, A2A_BASE_URL.
Los booleanos aceptan 1/true/yes/on (case-insensitive).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Union

from dotenv import load_dotenv


def _as_bool(value: Union[str, bool, None], default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: Union[str, int, None], default: int) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """Snapshot inmutable de la configuración de despliegue."""

    # Servidor Uvicorn (server.py)
    host: str = "127.0.0.1"
    port: int = 2024
    debug: bool = False
    log_level: str = "INFO"  # upper-case: server.py hace `.lower()` al pasarlo

    # A2A
    a2a_enabled: bool = True
    a2a_base_url: str = "http://127.0.0.1:2024"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Lee (una sola vez) la config desde el entorno y devuelve Settings.

    El cache hace que el montaje de agentes (app.main, infrastructure/a2a) y
    el server compartan el mismo snapshot; para forzar relectura en tests,
    se llama a `get_settings.cache_clear()`.
    """
    load_dotenv()  # sin override: el entorno real gana al .env local

    return Settings(
        host=os.getenv("HOST", "127.0.0.1"),
        port=_as_int(os.getenv("PORT"), 2024),
        debug=_as_bool(os.getenv("DEBUG"), False),
        log_level=str(os.getenv("LOG_LEVEL", "INFO")).upper(),
        a2a_enabled=_as_bool(os.getenv("A2A_ENABLED"), True),
        a2a_base_url=os.getenv("A2A_BASE_URL", "http://127.0.0.1:2024"),
    )