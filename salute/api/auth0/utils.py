from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache
from joserfc import jwt
from joserfc.errors import (
    BadSignatureError,
    DecodeError,
    ExpiredTokenError,
    InvalidClaimError,
    JoseError,
    MissingClaimError,
)
from joserfc.jwk import JWKRegistry, Key
from joserfc.jws import CompactSignature

from salute.api.auth0.types import Auth0TokenInfo


def _fetch_jwks(domain: str) -> list[dict[str, Any]]:
    try:
        resp = requests.get(f"https://{domain}/.well-known/jwks.json", timeout=2)
        resp.raise_for_status()
        data = resp.json()
        return data.get("keys", [])
    except (requests.RequestException, ValueError):
        # Handle network errors or JSON parsing errors
        # Log the error for debugging purposes
        # import logging
        # logger = logging.getLogger(__name__)
        # logger.error(f"Error fetching JWKS: {str(e)}")
        return []


def get_jwks() -> dict[str, dict[str, Any]]:
    auth0_domain = settings.AUTH0_DOMAIN  # type: ignore[misc]
    jwks_cache_key = f"AUTH0_JWKS__{auth0_domain}"

    # If we have cached keys, return them
    if keys := cache.get(jwks_cache_key):
        return keys

    new_keys = _fetch_jwks(auth0_domain)

    # If there aren't any keys, do not cache them.
    if not new_keys:
        return {}

    # Arrange the keys by Key ID
    key_dict = {key["kid"]: key for key in new_keys if "kid" in key}

    cache.set(jwks_cache_key, key_dict, timeout=settings.AUTH0_JWKS_CACHE_TIMEOUT)  # type: ignore[misc]
    return key_dict


def load_key(obj: CompactSignature) -> Key:
    """
    Load the specified key for the token.

    Use as jwt.decode(token, load_key)
    """
    headers = obj.headers()
    key_id = headers.get("kid")

    valid_keys = get_jwks()
    key = valid_keys.get(key_id)  # type: ignore[arg-type]
    if key is None:
        raise ValueError(f"Could not find key with ID: {key_id}")

    try:
        return JWKRegistry.import_key(key)
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"Invalid key format: {str(e)}") from e


def get_token_info(token: str) -> Auth0TokenInfo:
    """
    Decode and validate the JWT token, returning Auth0TokenInfo.

    Raises:
        ValueError: If the token is invalid, expired, or the signature is bad
        JoseError: If there's an issue with the JWT format
        ValidationError: If the claims don't meet validation rules
    """
    claims_requests = jwt.JWTClaimsRegistry(
        exp={"essential": True},
        iss={"essential": True, "value": f"https://{settings.AUTH0_DOMAIN}/"},  # type: ignore[misc]
        sub={"essential": True},
        scope={"essential": True},
        aud={"essential": True},
    )

    try:
        decoded_token = jwt.decode(token, load_key)  # type: ignore[arg-type]
        claims_requests.validate(decoded_token.claims)

        scope_list = decoded_token.claims.get("scope", "")
        scopes = scope_list.split(" ") if scope_list else []

        return Auth0TokenInfo(
            aud=decoded_token.claims.get("aud", ""),
            sub=decoded_token.claims.get("sub", ""),
            scopes=scopes,
        )
    except BadSignatureError as e:
        raise ValueError(f"Invalid token signature: {str(e)}") from e
    except DecodeError as e:
        raise ValueError(f"Invalid token signature: {str(e)}") from e
    except ExpiredTokenError as e:
        raise ValueError("Token has expired") from e
    except (MissingClaimError, InvalidClaimError) as e:
        raise ValueError(f"Invalid token claims: {str(e)}") from e
    except JoseError as e:
        raise ValueError(f"Invalid JWT format: {str(e)}") from e
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"Unexpected error validating token: {str(e)}") from e
