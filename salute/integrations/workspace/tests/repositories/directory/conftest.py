import pytest

from salute.integrations.workspace.repositories.directory._schema import (
    NameInfo,
    WorkspaceAccountInfo,
    WorkspaceGroupInfo,
)


@pytest.fixture
def sample_users() -> list[WorkspaceAccountInfo]:
    """Return sample users for testing."""
    return [
        WorkspaceAccountInfo(
            id=1,
            primaryEmail="user1@example.com",
            name=NameInfo(
                givenName="John",
                familyName="Doe",
                fullName="John Doe",
            ),
            isAdmin=False,
            isDelegatedAdmin=False,
            lastLoginTime="2023-01-01T12:00:00Z",
            creationTime="2023-01-01T12:00:00Z",
            agreedToTerms=True,
            suspended=False,
            archived=False,
            changePasswordAtNextLogin=False,
            orgUnitPath="/Users",
            isMailboxSetup=True,
            isEnrolledIn2Sv=True,
            isEnforcedIn2Sv=False,
            includeInGlobalAddressList=True,
        ),
        WorkspaceAccountInfo(
            id=2,
            primaryEmail="user2@example.com",
            name=NameInfo(
                givenName="Jane",
                familyName="Smith",
                fullName="Jane Smith",
            ),
            isAdmin=True,
            isDelegatedAdmin=False,
            lastLoginTime="2023-01-01T12:00:00Z",
            creationTime="2023-01-01T12:00:00Z",
            agreedToTerms=True,
            suspended=False,
            archived=False,
            changePasswordAtNextLogin=False,
            orgUnitPath="/Admins",
            isMailboxSetup=True,
            isEnrolledIn2Sv=True,
            isEnforcedIn2Sv=True,
            includeInGlobalAddressList=True,
        ),
    ]


@pytest.fixture
def sample_groups() -> list[WorkspaceGroupInfo]:
    """Return sample groups for testing."""
    return [
        WorkspaceGroupInfo(
            id="group1",
            email="group1@example.com",
            name="Group One",
            description="First test group",
            aliases=["group1-alias@example.com"],
        ),
        WorkspaceGroupInfo(
            id="group2",
            email="group2@example.com",
            name="Group Two",
            description="Second test group",
            aliases=[],
        ),
    ]
