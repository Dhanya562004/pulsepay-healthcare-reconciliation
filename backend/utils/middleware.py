import time
import uuid
import secrets
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from backend.utils.logger import logger
from backend.config import settings

class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware for tracing latency, tracking requests/responses,
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

class ApiKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware enforcing X-Api-Key header authentication across all endpoints
    except GET / (health check) and documentation pages (/docs, /redoc, /openapi.json).
    """
    EXEMPT_PATHS = {"/", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next) -> Response:
        # Allow CORS preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)

        # Allow GET / (health check)
        path = request.url.path
        if request.method == "GET" and path == "/":
            return await call_next(request)

        # Allow documentation pages
        if path in self.EXEMPT_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        # Check for X-Api-Key header
        api_key_header = request.headers.get("x-api-key")
        if not api_key_header:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing API Key. Provide 'X-Api-Key' header."}
            )

        expected_key = settings.API_KEY
        if not expected_key or not secrets.compare_digest(api_key_header, expected_key):
            return JSONResponse(
                status_code=403,
                content={"detail": "Forbidden: Invalid API Key."}
            )

        return await call_next(request)
