from typing import Annotated, Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt
from jose.utils import base64url_decode

from app.core.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser(dict[str, Any]):
    @property
    def username(self) -> str:
        return str(self.get("preferred_username") or self.get("sub") or "anonymous")


def _verify_signature(token: str, jwks: dict[str, Any]) -> None:
    headers = jwt.get_unverified_header(token)
    key = next((item for item in jwks["keys"] if item["kid"] == headers["kid"]), None)
    if key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown token key")
    message, encoded_signature = token.rsplit(".", 1)
    decoded_signature = base64url_decode(encoded_signature.encode())
    public_key = jwk.construct(key)
    if not public_key.verify(message.encode(), decoded_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token signature"
        )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CurrentUser:
    if not settings.auth_enabled:
        return CurrentUser(sub="local-dev", preferred_username="local-dev", roles=["admin"])
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = credentials.credentials
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            discovery = await client.get(
                f"{settings.keycloak_issuer}/.well-known/openid-configuration"
            )
            discovery.raise_for_status()
            jwks_response = await client.get(discovery.json()["jwks_uri"])
            jwks_response.raise_for_status()
        jwks = jwks_response.json()
        _verify_signature(token, jwks)
        claims = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=settings.keycloak_client_id,
            issuer=settings.keycloak_issuer,
        )
    except (httpx.HTTPError, JWTError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc
    return CurrentUser(claims)
