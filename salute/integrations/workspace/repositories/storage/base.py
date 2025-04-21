from typing import Literal, Protocol
from uuid import UUID

from pydantic import BaseModel

from salute.integrations.workspace.models import WorkspaceAccount
from salute.integrations.workspace.repositories.directory._schema import WorkspaceAccountInfo


class _WorkspaceAccountInfo(BaseModel):
    google_id: int
    salute_id: UUID
    primary_email: str


class UpdateOrCreateAccountResult(_WorkspaceAccountInfo, BaseModel):
    event_type: Literal["update_or_create_account"] = "update_or_create_account"
    created: bool


class SyncAccountAliasesResult(_WorkspaceAccountInfo, BaseModel):
    event_type: Literal["sync_workspace_account_aliases"] = "sync_workspace_account_aliases"
    aliases: list[str]
    removed_aliases: list[str]


class DeleteSpuriousAccountsResult(BaseModel):
    event_type: Literal["delete_spurious_workspace_accounts"] = "delete_spurious_workspace_accounts"
    deleted_accounts: list[_WorkspaceAccountInfo]


class StorageRepository(Protocol):
    def update_or_create_account(
        self, workspace_user: WorkspaceAccountInfo
    ) -> tuple[WorkspaceAccount, UpdateOrCreateAccountResult]: ...

    def sync_workspace_account_aliases(
        self, workspace_user: WorkspaceAccountInfo, *, account: WorkspaceAccount | None = None
    ) -> SyncAccountAliasesResult: ...

    def delete_spurious_workspace_accounts(
        self, known_users: list[WorkspaceAccountInfo]
    ) -> DeleteSpuriousAccountsResult | None: ...
