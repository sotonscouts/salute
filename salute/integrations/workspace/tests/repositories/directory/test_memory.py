import pytest

from salute.integrations.workspace.repositories.directory import (
    MemoryDirectoryRepository,
)
from salute.integrations.workspace.repositories.directory._schema import (
    WorkspaceAccountInfo,
    WorkspaceGroupInfo,
)


@pytest.mark.django_db
class TestMemoryDirectoryRepository:
    def test_init(self, sample_users: list[WorkspaceAccountInfo], sample_groups: list[WorkspaceGroupInfo]) -> None:
        """Test repository initialization with provided data."""
        repo = MemoryDirectoryRepository(
            users=sample_users,
            groups=sample_groups,
        )

        assert repo.users == sample_users
        assert repo.groups == sample_groups

    def test_list_users(self, sample_users: list[WorkspaceAccountInfo]) -> None:
        """Test listing users returns the provided user list."""
        repo = MemoryDirectoryRepository(
            users=sample_users,
            groups=[],
        )

        users = repo.list_users()

        assert users == sample_users
        assert len(users) == 2
        assert users[0].primary_email == "user1@example.com"
        assert users[1].primary_email == "user2@example.com"

    def test_list_groups(self, sample_groups: list[WorkspaceGroupInfo]) -> None:
        """Test listing groups returns the provided group list."""
        repo = MemoryDirectoryRepository(
            users=[],
            groups=sample_groups,
        )

        groups = repo.list_groups()

        assert groups == sample_groups
        assert len(groups) == 2
        assert groups[0].email == "group1@example.com"
        assert groups[1].email == "group2@example.com"
