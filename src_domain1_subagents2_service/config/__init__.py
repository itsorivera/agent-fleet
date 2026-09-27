"""Configuración del servicio (env) — no tocar desde el dominio.

Este paquete solo expone `config.settings.get_settings()`: la lectura del
entorno de despliegue (host/port/log, feature flags A2A) y nada más. El
dominio/application importa aquí para leer config; nunca al revés.
"""