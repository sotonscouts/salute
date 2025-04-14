from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from salute.integrations.workspace.repositories.directory._schema import (
    WorkspaceAccountInfo,
    WorkspaceGroupInfo,
)
from salute.integrations.workspace.repositories.directory.workspace import (
    DirectoryService,
    WorkspaceDirectoryRepository,
)


@pytest.fixture
def mock_credentials_file() -> str:
    """Create a dummy credentials file path for testing."""
    return "/path/to/fake/credentials.json"


@pytest.fixture
def mock_directory_service() -> tuple[MagicMock, MagicMock, MagicMock]:
    """Create a mock directory service for testing."""
    mock_service = MagicMock()

    # Setup users mock
    mock_users = MagicMock()
    mock_users_list = MagicMock()
    mock_users.return_value.list.return_value = mock_users_list

    # Setup groups mock
    mock_groups = MagicMock()
    mock_groups_list = MagicMock()
    mock_groups.return_value.list.return_value = mock_groups_list

    # Configure the service mock
    mock_service.users.return_value = mock_users
    mock_service.groups.return_value = mock_groups

    return mock_service, mock_users_list, mock_groups_list


@pytest.mark.django_db
class TestWorkspaceDirectoryRepository:
    @patch("salute.integrations.workspace.repositories.directory.workspace.service_account.Credentials")
    def test_init(self, mock_credentials_class: MagicMock, mock_credentials_file: str) -> None:
        """Test repository initialization."""
        # Setup mock credentials
        mock_creds = MagicMock()
        mock_credentials_class.from_service_account_file.return_value = mock_creds

        repo = WorkspaceDirectoryRepository(
            credentials_file_path=mock_credentials_file,
            delegated_actor="admin@example.com",
        )

        # Verify initialization
        assert repo.credentials_file_path == mock_credentials_file
        assert repo.delegated_actor == "admin@example.com"
        assert repo._credentials == mock_creds

        # Verify credentials were loaded correctly
        mock_credentials_class.from_service_account_file.assert_called_once_with(
            mock_credentials_file,
            scopes=WorkspaceDirectoryRepository.SCOPES,
        )

    @patch("salute.integrations.workspace.repositories.directory.workspace.service_account.Credentials")
    def test_get_credentials(self, mock_credentials_class: MagicMock, mock_credentials_file: str) -> None:
        """Test credentials are loaded from file."""
        mock_creds = MagicMock()
        mock_credentials_class.from_service_account_file.return_value = mock_creds

        repo = WorkspaceDirectoryRepository(
            credentials_file_path=mock_credentials_file,
            delegated_actor="admin@example.com",
        )

        mock_credentials_class.from_service_account_file.assert_called_once_with(
            mock_credentials_file,
            scopes=WorkspaceDirectoryRepository.SCOPES,
        )
        assert repo._credentials == mock_creds

    @patch("salute.integrations.workspace.repositories.directory.workspace.build")
    @patch("salute.integrations.workspace.repositories.directory.workspace.service_account.Credentials")
    def test_directory_service_property(
        self, mock_credentials_class: MagicMock, mock_build: MagicMock, mock_credentials_file: str
    ) -> None:
        """Test directory service property creates service with delegated credentials."""
        # Setup mocks
        mock_creds = MagicMock()
        mock_delegated_creds = MagicMock()
        mock_service = MagicMock()

        mock_credentials_class.from_service_account_file.return_value = mock_creds
        mock_creds.with_subject.return_value = mock_delegated_creds
        mock_build.return_value = mock_service

        # Create repository
        repo = WorkspaceDirectoryRepository(
            credentials_file_path=mock_credentials_file,
            delegated_actor="admin@example.com",
        )

        # Access property
        service = repo.directory_service

        # Verify behavior
        mock_creds.with_subject.assert_called_once_with("admin@example.com")
        mock_build.assert_called_once_with("admin", "directory_v1", credentials=mock_delegated_creds)

        # For NewType DirectoryService, we can't use isinstance
        # and _value is not the right access method.
        # Instead, verify that we can use it like the underlying service
        mock_users = MagicMock()
        mock_service.users.return_value = mock_users

        # This should work if service is properly created
        service.users()  # type: ignore[attr-defined]

        # Verify the service was accessed as expected
        mock_service.users.assert_called_once()

    @patch("salute.integrations.workspace.repositories.directory.workspace.service_account.Credentials")
    def test_list_users(
        self,
        mock_credentials_class: MagicMock,
        mock_credentials_file: str,
        sample_users: list[WorkspaceAccountInfo],
        mock_directory_service: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test listing users returns properly parsed results."""
        # Setup mocks
        mock_service, mock_users_list, _ = mock_directory_service
        mock_creds = MagicMock()
        mock_credentials_class.from_service_account_file.return_value = mock_creds

        # Setup mock for first API call
        mock_first_call = MagicMock()
        mock_first_call.execute.return_value = {
            "users": [sample_users[0].model_dump(by_alias=True)],
            "nextPageToken": "page2",
        }

        # Setup mock for second API call (with page token)
        mock_second_call = MagicMock()
        mock_second_call.execute.return_value = {
            "users": [sample_users[1].model_dump(by_alias=True)],
        }

        # Configure the users().list() call to return different mocks based on args
        def users_list_side_effect(**kwargs: Any) -> MagicMock:
            if "pageToken" in kwargs and kwargs["pageToken"] == "page2":
                return mock_second_call
            return mock_first_call

        # Apply the side effect
        mock_service.users.return_value.list.side_effect = users_list_side_effect

        # Create repository
        repo = WorkspaceDirectoryRepository(
            credentials_file_path=mock_credentials_file,
            delegated_actor="admin@example.com",
        )

        # Inject mock service directly
        repo.directory_service = DirectoryService(mock_service)

        # Call method
        users = repo.list_users()

        # Verify API calls
        mock_service.users.return_value.list.assert_any_call(customer="my_customer", maxResults=100)
        mock_service.users.return_value.list.assert_any_call(customer="my_customer", pageToken="page2", maxResults=100)

        # Check results
        assert len(users) == 2
        assert users[0].primary_email == sample_users[0].primary_email
        assert users[0].name.full_name == sample_users[0].name.full_name
        assert users[1].primary_email == sample_users[1].primary_email

    @patch("salute.integrations.workspace.repositories.directory.workspace.service_account.Credentials")
    def test_list_groups(
        self,
        mock_credentials_class: MagicMock,
        mock_credentials_file: str,
        sample_groups: list[WorkspaceGroupInfo],
        mock_directory_service: tuple[MagicMock, MagicMock, MagicMock],
    ) -> None:
        """Test listing groups returns properly parsed results."""
        # Setup mocks
        mock_service, _, mock_groups_list = mock_directory_service
        mock_creds = MagicMock()
        mock_credentials_class.from_service_account_file.return_value = mock_creds

        # Setup mock for first API call
        mock_first_call = MagicMock()
        mock_first_call.execute.return_value = {
            "groups": [sample_groups[0].model_dump(by_alias=True)],
            "nextPageToken": "page2",
        }

        # Setup mock for second API call (with page token)
        mock_second_call = MagicMock()
        mock_second_call.execute.return_value = {
            "groups": [sample_groups[1].model_dump(by_alias=True)],
        }

        # Configure the groups().list() call to return different mocks based on args
        def groups_list_side_effect(**kwargs: Any) -> MagicMock:
            if "pageToken" in kwargs and kwargs["pageToken"] == "page2":
                return mock_second_call
            return mock_first_call

        # Apply the side effect
        mock_service.groups.return_value.list.side_effect = groups_list_side_effect

        # Create repository
        repo = WorkspaceDirectoryRepository(
            credentials_file_path=mock_credentials_file,
            delegated_actor="admin@example.com",
        )

        # Inject mock service directly
        repo.directory_service = DirectoryService(mock_service)

        # Call method
        groups = repo.list_groups()

        # Verify API calls
        mock_service.groups.return_value.list.assert_any_call(customer="my_customer", maxResults=100)
        mock_service.groups.return_value.list.assert_any_call(customer="my_customer", pageToken="page2", maxResults=100)

        # Check results
        assert len(groups) == 2
        assert groups[0].email == sample_groups[0].email
        assert groups[0].name == sample_groups[0].name
        assert groups[1].email == sample_groups[1].email
