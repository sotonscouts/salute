from ._schema import WorkspaceAccountInfo, WorkspaceGroupInfo


class MemoryDirectoryRepository:
    def __init__(self, *, users: list[WorkspaceAccountInfo], groups: list[WorkspaceGroupInfo]) -> None:
        self.users = users
        self.groups = groups

    def list_users(self) -> list[WorkspaceAccountInfo]:
        return self.users

    def list_groups(self) -> list[WorkspaceGroupInfo]:
        return self.groups
