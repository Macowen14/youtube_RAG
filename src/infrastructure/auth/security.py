"""Supabase JWT authentication for FastAPI.

This module verifies Supabase-issued JWTs and extracts the authenticated
``user_id`` (the ``sub`` claim).  It is used as a FastAPI dependency across
all protected endpoints.

Authentication flow
-------------------
1. The frontend obtains a JWT from **Supabase Auth** (via ``@supabase/supabase-js``).
2. The JWT is sent to the backend in the ``Authorization: Bearer <token>`` header.
3. This module verifies the token using one of three strategies (in order):

   a. **JWKS (asymmetric)** — ES256/RS256 tokens verified against Supabase's
      published JWKS endpoint.
   b. **HS256 (symmetric)** — verified locally using ``SUPABASE_JWT_SECRET``.
   c. **Supabase Auth API fallback** — the token is validated by calling
      Supabase's ``/auth/v1/user`` endpoint directly.

4. On success the ``sub`` claim (a Supabase user UUID) is returned and
   injected into route handlers as ``user_id``.

Note
----
This module communicates with Supabase **only over HTTPS** — it has no
dependency on the PostgreSQL database and works independently of which
database provider is used (Neon, Supabase DB, local, etc.).
"""

from __future__ import annotations

import logging

import jwt
import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.infrastructure.config import Settings

logger = logging.getLogger(__name__)

settings = Settings()
security = HTTPBearer()

jwks_client = (
    jwt.PyJWKClient(
        f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    )
    if settings.supabase_url
    else None
)


# ---------------------------------------------------------------------------
# Public dependency
# ---------------------------------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """FastAPI dependency that returns the authenticated Supabase user ID.

    Raises :class:`~fastapi.HTTPException` with 401 status on failure.
    """
    token = credentials.credentials
    try:
        payload = _verify_supabase_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return user_id
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {exc}",
        ) from exc
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials with Supabase Auth: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# Token verification strategies
# ---------------------------------------------------------------------------

def _verify_supabase_token(token: str) -> dict:
    """Attempt to verify *token* using JWKS, then HS256, then the Auth API."""
    header = jwt.get_unverified_header(token)
    algorithm = header.get("alg")

    # Strategy 1: Asymmetric verification via Supabase JWKS endpoint.
    if algorithm in {"ES256", "RS256"}:
        if jwks_client is None:
            raise jwt.InvalidTokenError(
                "SUPABASE_URL is required to verify asymmetric Supabase JWTs."
            )
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=[algorithm],
            audience="authenticated",
            issuer=f"{settings.supabase_url.rstrip('/')}/auth/v1",
        )

    # Strategy 2: Symmetric HS256 verification using the shared secret.
    if algorithm == "HS256" and settings.supabase_jwt_secret:
        try:
            return jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
                issuer=f"{settings.supabase_url.rstrip('/')}/auth/v1",
            )
        except jwt.PyJWTError:
            logger.info("Local HS256 verification failed; falling back to Supabase Auth API.")

    # Strategy 3: Server-side validation via the Supabase Auth REST API.
    return _verify_with_supabase_auth(token)


def _verify_with_supabase_auth(token: str) -> dict:
    """Validate *token* by calling the Supabase ``/auth/v1/user`` endpoint."""
    if not settings.supabase_url or not settings.supabase_key:
        raise jwt.InvalidTokenError(
            "SUPABASE_URL and SUPABASE_KEY are required to verify Supabase JWTs."
        )

    response = requests.get(
        f"{settings.supabase_url.rstrip('/')}/auth/v1/user",
        headers={
            "apikey": settings.supabase_key,
            "Authorization": f"Bearer {token}",
        },
        timeout=10,
    )

    if response.status_code != 200:
        raise jwt.InvalidTokenError("Supabase Auth rejected the access token.")

    user = response.json()
    user_id = user.get("id")
    if not user_id:
        raise jwt.InvalidTokenError("Supabase Auth response did not include a user id.")

    return {"sub": user_id}
