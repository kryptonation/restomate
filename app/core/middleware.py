# app/core/middleware.py

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to all requests"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response
    

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Log request
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None
        )

        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log response
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                process_time=f"{process_time:.3f}s"
            )

            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            return response
        
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                process_time=f"{process_time:.3f}s"
            )
            raise


