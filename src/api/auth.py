"""Authentication and access control for Pactory Studio API.

Protects endpoints with STUDIO_PASSWORD or Bearer token when configured.
"""

import os
from typing import Optional
from fastapi import Header, HTTPException, status
from pydantic import BaseModel


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    authenticated: bool
    message: str


def get_configured_password() -> str:
    """Retrieve STUDIO_PASSWORD from environment or config."""
    return os.getenv("STUDIO_PASSWORD", "").strip()


async def verify_auth(
    x_studio_password: Optional[str] = Header(None, alias="x-studio-password"),
    authorization: Optional[str] = Header(None),
) -> bool:
    """FastAPI dependency to verify request authorization."""
    configured_pwd = get_configured_password()
    if not configured_pwd:
        # Development mode without password gate
        return True

    token = x_studio_password
    if not token and authorization:
        parts = authorization.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1].strip()
        else:
            token = authorization.strip()

    if token == configured_pwd:
        return True

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing studio authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
