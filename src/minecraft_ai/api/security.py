import logging
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

# --- API Key Authentication ---
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    """Verify the API key for protected endpoints.

    Returns the valid API key if validation passes, raises HTTPException if not.
    Requires MINECRAFT_AI_API_KEY environment variable to be set.
    """
    # Always read the key at runtime
    configured_key = os.getenv("MINECRAFT_AI_API_KEY")
    if not configured_key:
        logger.error("API key validation cannot proceed - MINECRAFT_AI_API_KEY not set in environment")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: API Key not configured.",
        )

    if not api_key:
        logger.warning("API key missing from request header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Please provide a key in the X-API-Key header.",
        )

    if api_key != configured_key:
        logger.warning("Invalid API key provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    return api_key
