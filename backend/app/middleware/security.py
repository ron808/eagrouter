# security middleware -- adds browser security headers and blocks oversized requests
# no rate limiting here since this is a private assignment app, not a public-facing api

import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("eagroute")

MAX_CONTENT_LENGTH = 1_048_576  # 1MB should be more than enough for any request here


class SecurityMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        # reject oversized requests before they waste any more resources
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_CONTENT_LENGTH:
            return JSONResponse(
                status_code=413,
                content={"error": "Request too large", "detail": "Max 1MB allowed"},
            )

        # let the actual request through
        response = await call_next(request)

        # tack on security headers -- tells browsers to be strict about content handling
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # strip the server header so we don't leak what we're running
        if "server" in response.headers:
            del response.headers["server"]

        return response
