# src/core/logging.py

"""
Centralized logging using structlog
Provides structured JSON logging for production and readable console logs for development
"""
import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from src.core.config import settings


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add application context to log entries.
    Extracts file, line number, and function name from call stack.
    """
    import structlog._frames

    frame, name = structlog._frames._find_first_app_frame_and_name(
        additional_ignores=["logging", __name__]
    )

    event_dict["file"] = frame.f_code.co_filename.split("/")[-1]
    event_dict["line"] = frame.f_lineno
    event_dict["function"] = frame.f_code.co_name

    return event_dict

def drop_color_message_key(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Drop 'color_message' key added by Uvicorn
    Uvicorn logs the message twice, we only need one
    """
    event_dict.pop("color_message", None)
    return event_dict

def censor_sensitive_data(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Censor sensitive data in logs.
    Replaces passwords, tokens, and API keys with asterisks.
    """
    sensitive_keys = {
        "password", "token", "api_key", "secret", "authorization",
        "refresh_token", "access_token", "session_id", "card_number",
        "cvv", "pin"
    }

    def censor_dict(d: dict) -> dict:
        """Recursively censor dictionary values"""
        censored = {}
        for key, value in d.items():
            if isinstance(value, dict):
                censored[key] = censor_dict(value)
            elif key.lower() in sensitive_keys:
                censored[key] = "***CENSORED***"
            else:
                censored[key] = value
        return censored
    
    return censor_dict(event_dict)

def setup_logging() -> None:
    """
    Configure structlog for the application
    Sets up processors, formatters, and log events
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=settings.log_level.upper(),
    )

    # Set log level for root logger
    logger = logging.getLogger()
    logger.setLevel(settings.log_level.upper())

    # Silence noisy loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Define processors based on environment
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        drop_color_message_key,
        censor_sensitive_data,
    ]

    # Add file/line info in development
    if settings.is_development:
        shared_processors.append(add_app_context)

    # Choose renderer based on environment
    if settings.log_format == "json" or settings.is_production:
        # JSON renderer for production
        renderer = structlog.processors.JSONRenderer()
    else:
        # Console renderer for development
        renderer = structlog.dev.ConsoleRenderer(
            colors=True, exception_formatter=structlog.dev.RichTracebackFormatter(),
        )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        cache_logger_on_first_use=True,
    )

    # Configure ProcessorFormatter for standard logging
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ]
    )

    # Apply formatter to all handlers
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.handlers = [handler]

    # Log configuration complete
    log = get_logger(__name__)
    log.info(
        "logging configured",
        environment=settings.environment,
        log_level=settings.log_level,
        log_format=settings.log_format,
    )


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
    """
    Get a logger instance

    Args:
        name: Logger name (usually __name__ of the module)

    Returns:
        Configured structlog logger

    Example:
        logger = get_logger(__name__)
        logger.info("User logged in", user_id=user.id, email=user.email)
    """
    return structlog.get_logger(name)


class LoggingMiddleware:
    """
    Middleware for logging HTTP requests and responses
    Adds correlation ID and request context to all logs
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        import uuid
        from time import time

        # Generate correlation ID
        correlation_id = str(uuid.uuid4())

        # Bind request context to logs
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            path=scope["path"],
            method=scope["method"],
            client_host=scope["client"][0] if scope.get("client") else None,
        )

        # Get logger
        logger = get_logger(__name__)

        # Record start time
        start_time = time()

        # Process request
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Bind response status
                structlog.contextvars.bind_contextvars(
                    status_code=message["status"]
                )

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            logger.error(
                "Request failed",
                error=str(e),
                error_type=type(e).__name__,
                duration=time() - start_time,
            )
            raise
        finally:
            # Log request completion
            duration = time() - start_time
            status_code = structlog.contextvars.get_contextvars().get("status_code", 0)

            # Determine log level based on status code
            if status_code >= 500:
                log_func = logger.error
            elif status_code >= 400:
                log_func = logger.warning
            else:
                log_func = logger.info

            # Skip health check logs in production
            if settings.is_production and scope["path"] in ["/health", "/healthz"]:
                return
            
            log_func(
                "Request completed",
                duration=f"{duration:.3f}s",
            )


            