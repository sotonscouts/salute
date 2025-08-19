from unittest.mock import Mock, patch

import pytest
import requests
from pydantic import ValidationError

from salute.integrations.osm.client import OSMClient, get_access_token
from salute.integrations.osm.schemata import OSMCountsResponse, OSMSection


def test_get_access_token() -> None:
    """Test that get_access_token works correctly."""
    mock_response = Mock()
    mock_response.json.return_value = {"access_token": "test-token"}

    with patch("requests.post", return_value=mock_response) as mock_post:
        token = get_access_token("client-id", "client-secret")
        assert token == "test-token"  # noqa: S105
        mock_post.assert_called_once_with(
            "https://www.onlinescoutmanager.co.uk/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "client-id",
                "client_secret": "client-secret",
                "scope": "section:administration:read",
            },
            timeout=30,
        )

    # Test invalid response
    mock_response.json.return_value = {}
    with patch("requests.post", return_value=mock_response), pytest.raises(ValidationError):
        get_access_token("client-id", "client-secret")


def test_osm_client_get_counts() -> None:
    """Test that OSMClient.get_counts works correctly."""
    client = OSMClient("test-token")

    mock_response = Mock()
    mock_response.json.return_value = {
        "district1": {
            "byGroup": {
                "group1": {
                    "sections": [
                        {
                            "sectionid": "123",
                            "name": "Test Section",
                            "numscouts": 10,
                            "numleaders": 2,
                        }
                    ]
                }
            }
        }
    }

    with patch.object(client.session, "request", return_value=mock_response) as mock_request:
        response = client.get_counts("test-section")
        assert isinstance(response, OSMCountsResponse)
        assert len(response.districts) == 1
        mock_request.assert_called_once_with(
            "GET",
            "https://www.onlinescoutmanager.co.uk/ext/discounts/?action=getSizes&code=118&sectionid=test-section",
        )

    # Test request failure
    mock_request = Mock(side_effect=requests.exceptions.HTTPError())
    with patch.object(client.session, "request", mock_request), pytest.raises(requests.exceptions.HTTPError):
        client.get_counts("test-section")

    # Test invalid response
    mock_response.json.return_value = {
        "district1": {
            "byGroup": {
                "group1": {
                    "sections": [
                        {
                            "sectionid": "123",
                            "name": "Test Section",
                            # Missing required numscouts field
                        }
                    ]
                }
            }
        }
    }
    with patch.object(client.session, "request", return_value=mock_response), pytest.raises(ValidationError):
        client.get_counts("test-section")


def test_osm_client_iter_sections() -> None:
    """Test that OSMClient.get_counts().iter_sections() works correctly."""
    client = OSMClient("test-token")

    mock_response = Mock()
    mock_response.json.return_value = {
        "district1": {
            "byGroup": {
                "group1": {
                    "sections": [
                        {
                            "sectionid": "123",
                            "name": "Test Section 1",
                            "numscouts": 10,
                            "numleaders": 2,
                        },
                        {
                            "sectionid": "456",
                            "name": "Test Section 2",
                            "numscouts": 15,
                            "numleaders": 3,
                        },
                    ]
                }
            }
        }
    }

    with patch.object(client.session, "request", return_value=mock_response):
        response = client.get_counts("test-section")
        sections = list(response.iter_sections())
        assert len(sections) == 2
        assert all(isinstance(section, OSMSection) for section in sections)
        assert sections[0].section_id == "123"
        assert sections[0].name == "Test Section 1"
        assert sections[1].section_id == "456"
        assert sections[1].name == "Test Section 2"
