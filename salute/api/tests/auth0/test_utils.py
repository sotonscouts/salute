"""
Tests for the Auth0 token validation utilities.
"""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest import mock
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests
from django.core.cache import cache
from django.test import override_settings
from joserfc.errors import (
    BadSignatureError,
    DecodeError,
    ExpiredTokenError,
    InvalidClaimError,
    JoseError,
    MissingClaimError,
)
from joserfc.jws import CompactSignature

from salute.api.auth0.utils import Auth0TokenInfo, _fetch_jwks, get_jwks, get_token_info, load_key


@pytest.fixture
def clear_cache() -> Generator[None, None, None]:
    """Clear cache before and after test."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def mock_jwks() -> dict[str, Any]:
    """Return mock JWKS for testing."""
    return {"keys": [{"kty": "RSA", "kid": "test-key-id", "use": "sig", "n": "test-n", "e": "AQAB"}]}


@pytest.fixture
def mock_compact_sig() -> mock.Mock:
    """Create a mock CompactSignature object for testing load_key."""
    mock_sig = Mock(spec=CompactSignature)
    mock_sig.headers.return_value = {"kid": "test-key-id"}
    return mock_sig


@pytest.fixture
def token_claims() -> dict[str, Any]:
    """Return standard token claims to use in tests."""
    now = datetime.now(UTC)
    return {
        "sub": "test-sub",
        "scope": "salute:user email",
        "iss": "https://test-domain.com/",
        "aud": "test-audience",
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "iat": int(now.timestamp()),
    }


class TestFetchJWKS:
    @patch("salute.api.auth0.utils.requests.get")
    def test_successful_fetch(self, mock_requests_get: mock.Mock) -> None:
        """Test successful JWKS fetch."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"keys": [{"kid": "test-key-id"}]}
        mock_requests_get.return_value = mock_response

        result = _fetch_jwks("test-domain.com")

        assert result == [{"kid": "test-key-id"}]
        mock_requests_get.assert_called_once_with("https://test-domain.com/.well-known/jwks.json", timeout=2)

    @patch("salute.api.auth0.utils.requests.get")
    def test_request_exception(self, mock_requests_get: mock.Mock) -> None:
        """Test request exception returns empty list."""
        mock_requests_get.side_effect = requests.RequestException("Error")

        result = _fetch_jwks("test-domain.com")

        assert result == []

    @patch("salute.api.auth0.utils.requests.get")
    def test_value_error(self, mock_requests_get: mock.Mock) -> None:
        """Test invalid JSON response returns empty list."""
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_requests_get.return_value = mock_response

        result = _fetch_jwks("test-domain.com")

        assert result == []

    @patch("salute.api.auth0.utils.requests.get")
    def test_empty_keys(self, mock_requests_get: mock.Mock) -> None:
        """Test empty keys in response returns empty list."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"other": "data"}
        mock_requests_get.return_value = mock_response

        result = _fetch_jwks("test-domain.com")

        assert result == []


class TestGetJWKS:
    @override_settings(AUTH0_DOMAIN="test-domain.com", AUTH0_JWKS_CACHE_TIMEOUT=60)
    @patch("salute.api.auth0.utils._fetch_jwks")
    def test_returns_cached_keys(
        self,
        mock_fetch_jwks: mock.Mock,
        clear_cache: Generator[None, None, None],
    ) -> None:
        """Test get_jwks returns cached keys if available."""
        # Set up cache
        cache.set("AUTH0_JWKS__test-domain.com", {"test-key-id": {"kid": "test-key-id"}}, 60)

        result = get_jwks()

        assert result == {"test-key-id": {"kid": "test-key-id"}}
        # Verify we didn't fetch new keys
        mock_fetch_jwks.assert_not_called()

    @override_settings(AUTH0_DOMAIN="test-domain.com", AUTH0_JWKS_CACHE_TIMEOUT=60)
    @patch("salute.api.auth0.utils._fetch_jwks")
    def test_fetches_and_caches_keys(
        self,
        mock_fetch_jwks: mock.Mock,
        clear_cache: Generator[None, None, None],
    ) -> None:
        """Test get_jwks fetches and caches keys when not cached."""
        mock_fetch_jwks.return_value = [{"kid": "test-key-id"}]

        result = get_jwks()

        assert result == {"test-key-id": {"kid": "test-key-id"}}
        mock_fetch_jwks.assert_called_once_with("test-domain.com")
        assert cache.get("AUTH0_JWKS__test-domain.com") == {"test-key-id": {"kid": "test-key-id"}}

    @override_settings(AUTH0_DOMAIN="test-domain.com", AUTH0_JWKS_CACHE_TIMEOUT=60)
    @patch("salute.api.auth0.utils._fetch_jwks")
    def test_empty_response_not_cached(
        self,
        mock_fetch_jwks: mock.Mock,
        clear_cache: Generator[None, None, None],
    ) -> None:
        """Test empty response is not cached."""
        mock_fetch_jwks.return_value = []

        result = get_jwks()

        assert result == {}
        assert cache.get("AUTH0_JWKS__test-domain.com") is None

    @override_settings(AUTH0_DOMAIN="test-domain.com", AUTH0_JWKS_CACHE_TIMEOUT=60)
    @patch("salute.api.auth0.utils._fetch_jwks")
    def test_filters_keys_without_kid(
        self,
        mock_fetch_jwks: mock.Mock,
        clear_cache: Generator[None, None, None],
    ) -> None:
        """Test keys without kid are filtered out."""
        mock_fetch_jwks.return_value = [
            {"kid": "test-key-id", "other": "value"},
            {"other": "value"},  # No kid
        ]

        result = get_jwks()

        assert result == {"test-key-id": {"kid": "test-key-id", "other": "value"}}


class TestLoadKey:
    @patch("salute.api.auth0.utils.get_jwks")
    @patch("salute.api.auth0.utils.JWKRegistry.import_key")
    def test_successful_key_load(
        self,
        mock_import_key: mock.Mock,
        mock_get_jwks: mock.Mock,
        mock_compact_sig: mock.Mock,
    ) -> None:
        """Test successful key load."""
        mock_get_jwks.return_value = {"test-key-id": {"kid": "test-key-id"}}
        mock_key = MagicMock()
        mock_import_key.return_value = mock_key

        result = load_key(mock_compact_sig)

        assert result == mock_key
        mock_import_key.assert_called_once_with({"kid": "test-key-id"})

    @patch("salute.api.auth0.utils.get_jwks")
    def test_key_not_found(self, mock_get_jwks: mock.Mock, mock_compact_sig: mock.Mock) -> None:
        """Test error when key not found."""
        mock_get_jwks.return_value = {}

        with pytest.raises(ValueError) as excinfo:
            load_key(mock_compact_sig)

        assert "Could not find key with ID: test-key-id" in str(excinfo.value)

    @patch("salute.api.auth0.utils.get_jwks")
    @patch("salute.api.auth0.utils.JWKRegistry.import_key")
    def test_key_import_error(
        self,
        mock_import_key: mock.Mock,
        mock_get_jwks: mock.Mock,
        mock_compact_sig: mock.Mock,
    ) -> None:
        """Test error when key import fails."""
        mock_get_jwks.return_value = {"test-key-id": {"kid": "test-key-id"}}
        mock_import_key.side_effect = Exception("Import error")

        with pytest.raises(ValueError) as excinfo:
            load_key(mock_compact_sig)

        assert "Invalid key format" in str(excinfo.value)


class TestGetTokenInfo:
    @override_settings(AUTH0_DOMAIN="test-domain.com", AUTH0_AUDIENCE="test-audience")
    @patch("salute.api.auth0.utils.jwt.decode")
    @patch("salute.api.auth0.utils.load_key")
    def test_successful_token_decode(
        self,
        mock_load_key: mock.Mock,
        mock_decode: mock.Mock,
        token_claims: dict[str, Any],
    ) -> None:
        """Test successful token decoding."""
        # Setup mock
        mock_token = MagicMock()
        mock_token.claims = token_claims
        mock_decode.return_value = mock_token

        # Call function
        result = get_token_info("test-token")

        # Verify result
        assert isinstance(result, Auth0TokenInfo)
        assert result.sub == "test-sub"
        assert result.scopes == ["salute:user", "email"]

    @override_settings(AUTH0_DOMAIN="test-domain.com", AUTH0_AUDIENCE="test-audience")
    @patch("salute.api.auth0.utils.jwt.decode")
    @patch("salute.api.auth0.utils.load_key")
    def test_invalid_signature(self, mock_load_key: mock.Mock, mock_decode: mock.Mock) -> None:
        """Test invalid signature error."""
        mock_decode.side_effect = BadSignatureError("Invalid signature")

        with pytest.raises(ValueError) as excinfo:
            get_token_info("test-token")

        assert "Invalid token signature" in str(excinfo.value)

    @override_settings(AUTH0_DOMAIN="test-domain.com", AUTH0_AUDIENCE="test-audience")
    @patch("salute.api.auth0.utils.jwt.decode")
    @patch("salute.api.auth0.utils.load_key")
    def test_decode_error(self, mock_load_key: mock.Mock, mock_decode: mock.Mock) -> None:
        """Test decode error."""
        mock_decode.side_effect = DecodeError("Decode error")

        with pytest.raises(ValueError) as excinfo:
            get_token_info("test-token")

        assert "Invalid token signature" in str(excinfo.value)

    @override_settings(AUTH0_DOMAIN="test-domain.com", AUTH0_AUDIENCE="test-audience")
    @patch("salute.api.auth0.utils.jwt.decode")
    @patch("salute.api.auth0.utils.load_key")
    def test_expired_token(self, mock_load_key: mock.Mock, mock_decode: mock.Mock) -> None:
        """Test expired token error."""
        mock_decode.side_effect = ExpiredTokenError("Token expired")

        with pytest.raises(ValueError) as excinfo:
            get_token_info("test-token")

        assert "Token has expired" in str(excinfo.value)

    @override_settings(AUTH0_DOMAIN="test-domain.com", AUTH0_AUDIENCE="test-audience")
    @patch("salute.api.auth0.utils.jwt.decode")
    @patch("salute.api.auth0.utils.load_key")
    def test_missing_claim(self, mock_load_key: mock.Mock, mock_decode: mock.Mock) -> None:
        """Test missing claim error."""
        mock_decode.side_effect = MissingClaimError("Missing claim")

        with pytest.raises(ValueError) as excinfo:
            get_token_info("test-token")

        assert "Invalid token claims" in str(excinfo.value)

    @override_settings(AUTH0_DOMAIN="test-domain.com", AUTH0_AUDIENCE="test-audience")
    @patch("salute.api.auth0.utils.jwt.decode")
    @patch("salute.api.auth0.utils.load_key")
    def test_invalid_claim(self, mock_load_key: mock.Mock, mock_decode: mock.Mock) -> None:
        """Test invalid claim error."""
        mock_decode.side_effect = InvalidClaimError("Invalid claim")

        with pytest.raises(ValueError) as excinfo:
            get_token_info("test-token")

        assert "Invalid token claims" in str(excinfo.value)

    @override_settings(AUTH0_DOMAIN="test-domain.com", AUTH0_AUDIENCE="test-audience")
    @patch("salute.api.auth0.utils.jwt.decode")
    @patch("salute.api.auth0.utils.load_key")
    def test_jwt_error(self, mock_load_key: mock.Mock, mock_decode: mock.Mock) -> None:
        """Test JWT format error."""
        mock_decode.side_effect = JoseError("Invalid JWT")

        with pytest.raises(ValueError) as excinfo:
            get_token_info("test-token")

        assert "Invalid JWT format" in str(excinfo.value)

    @override_settings(AUTH0_DOMAIN="test-domain.com", AUTH0_AUDIENCE="test-audience")
    @patch("salute.api.auth0.utils.jwt.decode")
    @patch("salute.api.auth0.utils.load_key")
    def test_empty_scope(self, mock_load_key: mock.Mock, mock_decode: mock.Mock, token_claims: dict[str, Any]) -> None:
        """Test empty scope claim is rejected."""
        # Setup claims validation to fail for empty scope
        mock_decode.side_effect = InvalidClaimError("Invalid claim: scope")

        with pytest.raises(ValueError) as excinfo:
            get_token_info("test-token")

        assert "Invalid token claims" in str(excinfo.value)
        assert "scope" in str(excinfo.value)

    @override_settings(AUTH0_DOMAIN="test-domain.com", AUTH0_AUDIENCE="test-audience")
    @patch("salute.api.auth0.utils.jwt.decode")
    @patch("salute.api.auth0.utils.load_key")
    def test_missing_scope_field(
        self,
        mock_load_key: mock.Mock,
        mock_decode: mock.Mock,
        token_claims: dict[str, Any],
    ) -> None:
        """Test missing scope claim is rejected."""
        # Setup claims validation to fail for missing scope
        mock_decode.side_effect = MissingClaimError("Missing claim: scope")

        with pytest.raises(ValueError) as excinfo:
            get_token_info("test-token")

        assert "Invalid token claims" in str(excinfo.value)
        assert "scope" in str(excinfo.value)
