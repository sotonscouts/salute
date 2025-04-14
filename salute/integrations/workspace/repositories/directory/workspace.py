from functools import cached_property
from typing import NewType

from google.oauth2 import service_account
from googleapiclient.discovery import build
from pydantic import TypeAdapter

from ._schema import WorkspaceAccountInfo, WorkspaceGroupInfo

DirectoryService = NewType("DirectoryService", object)


class WorkspaceDirectoryRepository:
    SCOPES = [
        "https://www.googleapis.com/auth/admin.directory.user",
        "https://www.googleapis.com/auth/admin.directory.group",
    ]

    def __init__(
        self,
        *,
        credentials_file_path: str,
        delegated_actor: str,
    ) -> None:
        self.credentials_file_path = credentials_file_path
        self.delegated_actor = delegated_actor

        self._credentials = self._get_credentials()

    def _get_credentials(self) -> service_account.Credentials:
        return service_account.Credentials.from_service_account_file(  # type: ignore
            self.credentials_file_path,
            scopes=self.SCOPES,
        )

    @cached_property
    def directory_service(self) -> DirectoryService:
        delegated_credentials = self._credentials.with_subject(self.delegated_actor)  # type: ignore
        service = build("admin", "directory_v1", credentials=delegated_credentials)
        return DirectoryService(service)

    def list_users(self) -> list[WorkspaceAccountInfo]:
        results = self.directory_service.users().list(customer="my_customer", maxResults=100).execute()  # type: ignore[attr-defined]
        users = results.get("users", [])

        # Iterate through pages
        while "nextPageToken" in results:
            page_token = results["nextPageToken"]
            results = (
                self.directory_service.users()  # type: ignore[attr-defined]
                .list(customer="my_customer", pageToken=page_token, maxResults=100)
                .execute()
            )
            users.extend(results.get("users", []))

        ta = TypeAdapter(list[WorkspaceAccountInfo])
        return ta.validate_python(users)

    def list_groups(self) -> list[WorkspaceGroupInfo]:
        results = self.directory_service.groups().list(customer="my_customer", maxResults=100).execute()  # type: ignore[attr-defined]
        groups = results.get("groups", [])

        # Iterate through pages
        while "nextPageToken" in results:
            page_token = results["nextPageToken"]
            results = (
                self.directory_service.groups()  # type: ignore[attr-defined]
                .list(customer="my_customer", pageToken=page_token, maxResults=100)
                .execute()
            )
            groups.extend(results.get("groups", []))

        ta = TypeAdapter(list[WorkspaceGroupInfo])
        return ta.validate_python(groups)
