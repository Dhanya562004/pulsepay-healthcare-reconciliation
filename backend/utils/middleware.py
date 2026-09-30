import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from backend.utils.logger import logger

class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Production middleware for tracing latency, tracking requests/responses,
    and capturing execution metrics for observability.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        start_time = time.time()

        # Log request entry
        logger.info(f"[{request_id}] START {request.method} {request.url.path}")

        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000  # Latency in milliseconds
            
            # Attach custom telemetry headers
            response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
            response.headers["X-Request-ID"] = request_id

            logger.info(
                f"[{request_id}] END {request.method} {request.url.path} "
                f"Status: {response.status_code} | Duration: {process_time:.2f}ms"
            )
            return response
        except Exception as exc:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"[{request_id}] EXCEPTION {request.method} {request.url.path} "
                f"Error: {str(exc)} | Duration: {process_time:.2f}ms"
            )
            raise exc
