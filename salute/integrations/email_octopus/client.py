import time
from typing import Any

import requests

from .schemata import (
    BulkUpdateContactsRequest,
    Contact,
    ContactsResponse,
    ContactStatus,
    CreateContactRequest,
    UpdateContactItem,
)

EO_BASE_URL = "https://api.emailoctopus.com"


class EmailOctopusClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
            }
        )

    def _request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        """Make a request to the Email Octopus API with automatic rate limit handling.

        Implements retry logic for 429 (rate limit) responses using exponential backoff.
        """
        max_retries = 5
        base_delay = 0.1  # Start with 100ms delay

        for attempt in range(max_retries):
            response = self.session.request(method, EO_BASE_URL + url, **kwargs)

            # Check rate limiting header
            remaining = response.headers.get("X-RateLimiting-Remaining")

            # If we hit rate limit, retry with exponential backoff
            if response.status_code == 429:
                if attempt < max_retries - 1:
                    # Calculate delay: exponential backoff with jitter
                    delay = base_delay * (2**attempt)
                    print(f"Rate limit hit (429). Retrying in {delay:.2f}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    # Last attempt, raise the error
                    response.raise_for_status()

            # For error responses, try to include the response body in the error message
            if not response.ok:
                try:
                    error_data = response.json()
                    print(f"API Error {response.status_code}: {error_data}")
                except Exception:  # noqa: BLE001
                    print(f"API Error {response.status_code}: {response.text}")

            # For successful responses, raise any other HTTP errors
            response.raise_for_status()

            # Optional: warn if we're getting close to rate limit
            if remaining and int(remaining) < 10:
                print(f"Warning: Only {remaining} API tokens remaining")

            return response

        # This shouldn't be reached, but just in case
        response.raise_for_status()
        return response

    def get_all_contacts_for_status(self, list_id: str, *, status: ContactStatus = "subscribed") -> list[Contact]:
        """Get all contacts from a list, handling pagination automatically.

        Args:
            list_id: The Email Octopus list ID
            status: Optional status to filter contacts by

        Returns:
            A list of all validated Contact objects from the list

        Raises:
            requests.exceptions.HTTPError: If the API request fails
            pydantic.ValidationError: If the API response is not valid
        """
        contacts = []
        starting_after = None

        while True:
            url = f"/lists/{list_id}/contacts"
            params: dict[str, Any] = {"limit": 100, "status": status}
            if starting_after:
                params["starting_after"] = starting_after

            response = self._request("GET", url, params=params)
            response_data = response.json()

            contacts_response = ContactsResponse.model_validate(response_data)
            contacts.extend(contacts_response.data)

            next_page = contacts_response.paging.get("next", {})
            starting_after = next_page.get("starting_after")

            if not starting_after:
                break

        return contacts

    def get_all_contacts(self, list_id: str) -> list[Contact]:
        """Get all contacts from a list, regardless of status.

        Args:
            list_id: The Email Octopus list ID
        Returns:
            A list of all validated Contact objects from the list
        """
        all_contacts = []
        all_statuses: list[ContactStatus] = ["pending", "subscribed", "unsubscribed"]
        for status in all_statuses:
            contacts_for_status = self.get_all_contacts_for_status(list_id, status=status)
            all_contacts.extend(contacts_for_status)
        return all_contacts

    def get_contact(self, list_id: str, contact_id: str) -> Contact:
        """Get a single contact by ID.

        Args:
            list_id: The Email Octopus list ID
            contact_id: The contact ID to retrieve

        Returns:
            A validated Contact object for the requested contact

        Raises:
            requests.exceptions.HTTPError: If the API request fails
            pydantic.ValidationError: If the API response is not valid
        """
        url = f"/lists/{list_id}/contacts/{contact_id}"
        response = self._request("GET", url)
        return Contact.model_validate(response.json())

    def create_contact(
        self,
        list_id: str,
        email_address: str,
        fields: dict[str, str] | None = None,
        tags: list[str] | None = None,
        status: ContactStatus | None = None,
    ) -> Contact:
        """Create a new contact in a list.

        Args:
            list_id: The Email Octopus list ID
            email_address: The email address of the contact
            fields: Optional dict of custom field key/value pairs (using field tags as keys)
            tags: Optional list of tags to associate with the contact
            status: Optional status for the contact ("pending", "subscribed", or "unsubscribed")

        Returns:
            A validated Contact object for the newly created contact

        Raises:
            requests.exceptions.HTTPError: If the API request fails
            pydantic.ValidationError: If the request data or response is not valid
        """
        url = f"/lists/{list_id}/contacts"

        request_data = CreateContactRequest(
            email_address=email_address,
            fields=fields,
            tags=tags,
            status=status,
        )

        payload = request_data.model_dump(exclude_none=True, by_alias=True)

        response = self._request(
            "POST",
            url,
            json=payload,
        )

        return Contact.model_validate(response.json())

    def update_contact(
        self,
        list_id: str,
        contact_id: str,
        email_address: str | None = None,
        fields: dict[str, str] | None = None,
        tags: list[str] | None = None,
        status: ContactStatus | None = None,
    ) -> Contact:
        """Update an existing contact in a list.

        Args:
            list_id: The Email Octopus list ID
            contact_id: The contact ID to update
            email_address: Optional new email address for the contact
            fields: Optional dict of custom field key/value pairs (using field tags as keys)
            tags: Optional list of tags to associate with the contact
            status: Optional status for the contact ("pending", "subscribed", or "unsubscribed")

        Returns:
            A validated Contact object for the updated contact

        Raises:
            requests.exceptions.HTTPError: If the API request fails
            pydantic.ValidationError: If the request data or response is not valid
        """
        url = f"/lists/{list_id}/contacts/{contact_id}"

        # Build update payload - only include fields that are provided
        update_data: dict[str, Any] = {}
        if email_address is not None:
            update_data["email_address"] = email_address
        if fields is not None:
            update_data["fields"] = fields
        if tags is not None:
            update_data["tags"] = tags
        if status is not None:
            update_data["status"] = status

        response = self._request("PUT", url, json=update_data)
        return Contact.model_validate(response.json())

    def bulk_update_contacts(
        self,
        list_id: str,
        updates: list[UpdateContactItem],
    ) -> None:
        """Bulk update multiple contacts in a list.

        Args:
            list_id: The Email Octopus list ID
            updates: List of UpdateContactItem objects with contact IDs and fields to update

        Raises:
            requests.exceptions.HTTPError: If the API request fails
            pydantic.ValidationError: If the request data is not valid
        """
        url = f"/lists/{list_id}/contacts/batch"

        request_data = BulkUpdateContactsRequest(contacts=updates)
        payload = request_data.model_dump(exclude_none=True, mode="json")

        response = self._request("PUT", url, json=payload)
        response.raise_for_status()

    def delete_contact(self, list_id: str, contact_id: str) -> None:
        """Delete a contact from a list.

        Args:
            list_id: The Email Octopus list ID
            contact_id: The contact ID to delete

        Raises:
            requests.exceptions.HTTPError: If the API request fails
        """
        url = f"/lists/{list_id}/contacts/{contact_id}"
        response = self._request("DELETE", url)
        response.raise_for_status()
