from typing import Any

import requests
from pydantic import BaseModel

from .schemata import OSMCountsResponse

OSM_BASE_URL = "https://www.onlinescoutmanager.co.uk"
OSM_TOKEN_URL = f"{OSM_BASE_URL}/oauth/token"
OSM_SCOPES = "section:administration:read"


class OSMTokenResponse(BaseModel):
    """Schema for the OSM token response."""

    access_token: str


def get_access_token(client_id: str, client_secret: str) -> str:
    """Get an access token from OSM.

    Args:
        client_id: The OSM client ID
        client_secret: The OSM client secret

    Returns:
        The access token

    Raises:
        requests.exceptions.HTTPError: If the API request fails
        pydantic.ValidationError: If the API response is not valid
    """
    url = OSM_TOKEN_URL
    response = requests.post(
        url,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": OSM_SCOPES,
        },
        timeout=30,
    )
    response.raise_for_status()
    return OSMTokenResponse.model_validate(response.json()).access_token


class OSMClient:
    def __init__(self, bearer_token: str, base_url: str = "https://www.onlinescoutmanager.co.uk") -> None:
        self.bearer_token = bearer_token
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.bearer_token}",
            }
        )

    def _request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        response = self.session.request(method, self.base_url + url, **kwargs)
        response.raise_for_status()
        return response

    def get_counts(self, section_id: str) -> OSMCountsResponse:
        """Get section counts from OSM.

        Args:
            section_id: The OSM section ID to get counts for

        Returns:
            A validated OSMCountsResponse object containing the section counts data

        Raises:
            requests.exceptions.HTTPError: If the API request fails
            pydantic.ValidationError: If the API response is not valid
        """
        url = f"/ext/discounts/?action=getSizes&code=118&sectionid={section_id}"
        response = self._request("GET", url)
        return OSMCountsResponse.model_validate_api_response(response.json())
