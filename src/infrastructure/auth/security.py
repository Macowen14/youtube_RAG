import logging

import jwt
import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.infrastructure.config import Settings

settings = Settings()
security = HTTPBearer()
jwks_client = jwt.PyJWKClient(f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json") if settings.supabase_url else None

logger = logging.getLogger(__name__)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    token = credentials.credentials
    try:
        payload = _verify_supabase_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return user_id
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
        )
    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials with Supabase Auth: {str(e)}",
        )


def _verify_supabase_token(token: str) -> dict:
    header = jwt.get_unverified_header(token)
    algorithm = header.get("alg")

    if algorithm in {"ES256", "RS256"}:
        if jwks_client is None:
            raise jwt.InvalidTokenError("SUPABASE_URL is required to verify asymmetric Supabase JWTs.")

        signing_key = jwks_client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=[algorithm],
            audience="authenticated",
            issuer=f"{settings.supabase_url.rstrip('/')}/auth/v1",
        )

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
            logger.info("Local HS256 verification failed; falling back to Supabase Auth.")

    return _verify_with_supabase_auth(token)


def _verify_with_supabase_auth(token: str) -> dict:
    if not settings.supabase_url or not settings.supabase_key:
        raise jwt.InvalidTokenError("SUPABASE_URL and SUPABASE_KEY are required to verify Supabase JWTs.")

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
