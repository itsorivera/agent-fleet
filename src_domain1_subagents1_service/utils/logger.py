"""Logger estructurado (structlog) con correlation_id en contextvars."""

import logging
import sys

import structlog

_is_configured = False


def set_correlation_id(correlation_id: str) -> None:
    """Sets the correlation_id for the current execution context."""
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)


def set_context_vars(**kwargs) -> None:
    """Binds arbitrary variables (user_id, etc.) to the log context."""
    structlog.contextvars.bind_contextvars(**kwargs)


def get_correlation_id() -> str:
    """Retrieves the current correlation_id from context."""
    return structlog.contextvars.get_contextvars().get("correlation_id", "no-id")


def setup_logger(json_format: bool = False, level: str = "INFO") -> None:
    """Configures structlog and standard logging (idempotente)."""
    global _is_configured
    if _is_configured:
        return

    # Standardize log level
    log_level = getattr(logging, level.upper(), logging.INFO)

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Redirect standard logging to structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # When app level is DEBUG, these libraries become too chatty.
    for logger_name in [
        "botocore",
        "boto3",
        "urllib3",
        "asyncio",
        "httpx",
        "uvicorn.access",
        "uvicorn.error",
    ]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    _is_configured = True


def get_logger(name: str):
    if not _is_configured:
        setup_logger(level="INFO")
    return structlog.get_logger(name)