import logging
import os
import time
from collections import deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


logger = logging.getLogger("kintraffic.security")


class SecurityMiddleware(BaseHTTPMiddleware):

    def __init__(self, app):
        super().__init__(app)

        self.window_seconds = 60

        self.read_limit = int(
            os.getenv(
                "KINTRAFFIC_RATE_LIMIT_PER_MINUTE",
                "180",
            )
        )

        self.write_limit = int(
            os.getenv(
                "KINTRAFFIC_WRITE_RATE_LIMIT_PER_MINUTE",
                "30",
            )
        )

        self.buckets = {}


    def get_client_id(self, request):

        forwarded = request.headers.get(
            "x-forwarded-for"
        )

        if forwarded:
            return forwarded.split(",")[0].strip()

        if request.client:
            return request.client.host

        return "unknown"


    def check_rate_limit(
        self,
        key,
        limit,
    ):
        now = time.monotonic()

        bucket = self.buckets.setdefault(
            key,
            deque(),
        )

        while (
            bucket
            and now - bucket[0]
            >= self.window_seconds
        ):
            bucket.popleft()

        if len(bucket) >= limit:
            return False

        bucket.append(now)

        return True


    async def dispatch(
        self,
        request,
        call_next,
    ):

        path = request.url.path
        method = request.method.upper()

        docs_enabled = (
            os.getenv(
                "KINTRAFFIC_DOCS_ENABLED",
                "false",
            ).lower()
            == "true"
        )

        protected_docs = {
            "/docs",
            "/docs/",
            "/redoc",
            "/redoc/",
            "/openapi.json",
        }

        if (
            path in protected_docs
            and not docs_enabled
        ):
            return JSONResponse(
                status_code=404,
                content={
                    "detail": "Not Found"
                },
            )


        client_id = self.get_client_id(
            request
        )

        is_write = method in {
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
        }

        if is_write:
            limit = self.write_limit
            scope = "write"

        else:
            limit = self.read_limit
            scope = "read"


        allowed = self.check_rate_limit(
            f"{scope}:{client_id}",
            limit,
        )

        if not allowed:

            logger.warning(
                "rate_limit_exceeded method=%s path=%s",
                method,
                path,
            )

            return JSONResponse(
                status_code=429,
                content={
                    "detail":
                        "Too many requests"
                },
                headers={
                    "Retry-After": "60"
                },
            )


        response = await call_next(
            request
        )


        if is_write:

            logger.info(
                "write_request method=%s path=%s status=%s",
                method,
                path,
                response.status_code,
            )


        return response
