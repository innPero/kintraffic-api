import os
import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader


api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
)


def verify_api_key(
    api_key: str | None = Security(api_key_header),
):
    expected_key = os.getenv(
        "KINTRAFFIC_API_KEY"
    )

    if not expected_key:
        raise HTTPException(
            status_code=503,
            detail="API security is not configured",
        )

    if (
        not api_key
        or not secrets.compare_digest(
            api_key,
            expected_key,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )

    return api_key