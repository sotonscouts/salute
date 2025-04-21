from typing import Protocol

from ._schema import WorkspaceAccountInfo, WorkspaceGroupInfo


class DirectoryRepository(Protocol):
    def list_users(self) -> list[WorkspaceAccountInfo]: ...

    def list_groups(self) -> list[WorkspaceGroupInfo]: ...
