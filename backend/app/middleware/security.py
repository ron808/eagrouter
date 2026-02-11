# security middleware - adds security headers and blocks oversized requests
# no rate limiting here since this is a private assignment, not a public api

import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("eagroute")

MAX_CONTENT_LENGTH = 1_048_576  # 1MB, nobody should be sending more than this


class SecurityMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        # check request size before doing anything else
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_CONTENT_LENGTH:
            return JSONResponse(
                status_code=413,
                content={"error": "Request too large", "detail": "Max 1MB allowed"},
            )

        # let the actual request through
        response = await call_next(request)

        # slap on security headers - these tell browsers to behave
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # don't leak what server we're running
        if "server" in response.headers:
            del response.headers["server"]

        return response
