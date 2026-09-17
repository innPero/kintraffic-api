import os
import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader


ingest_key_header = APIKeyHeader(
    name="X-Ingest-Key",
    auto_error=False,
)


admin_key_header = APIKeyHeader(
    name="X-Admin-Key",
    auto_error=False,
)


def verify_ingest_key(
    api_key: str | None = Security(
        ingest_key_header
    ),
):
    expected_key = os.getenv(
        "KINTRAFFIC_INGEST_KEY"
    )

    if not expected_key:
        raise HTTPException(
            status_code=503,
            detail=(
                "Ingest security is not configured"
            ),
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
            detail=(
                "Invalid or missing ingest key"
            ),
        )

    return api_key


def verify_admin_key(
    api_key: str | None = Security(
        admin_key_header
    ),
):
    expected_key = os.getenv(
        "KINTRAFFIC_ADMIN_KEY"
    )

    if not expected_key:
        raise HTTPException(
            status_code=503,
            detail=(
                "Admin security is not configured"
            ),
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
            detail=(
                "Invalid or missing admin key"
            ),
        )

    return api_key
