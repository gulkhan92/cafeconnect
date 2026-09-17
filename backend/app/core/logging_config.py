import json
import logging
import sys
import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("cafeconnect")


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Anything passed via logger.info(..., extra={...}) rides along as-is.
        for key, value in record.__dict__.get("extra_fields", {}).items():
            payload[key] = value
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Simple structured (JSON-lines) logging to stdout.

    No external logging service is required: every free-tier host (Render,
    Railway, Fly.io) captures stdout and makes it searchable, which is what
    the plan calls for when no dedicated logging destination is configured.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


def log_event(message: str, **fields) -> None:
    logger.info(message, extra={"extra_fields": fields})


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs one structured line per request: request id, method, path,
    status, latency, and the user id if the route resolved one (set on
    request.state by get_current_user / get_current_user_optional)."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id
        request.state.user_id = None

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            log_event(
                "request_failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                user_id=getattr(request.state, "user_id", None),
                latency_ms=latency_ms,
            )
            raise

        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        log_event(
            "request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            user_id=getattr(request.state, "user_id", None),
            latency_ms=latency_ms,
        )
        return response
