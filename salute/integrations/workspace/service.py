from functools import cached_property

from tqdm import tqdm

from salute.integrations.workspace.repositories.directory import DirectoryRepository, WorkspaceDirectoryRepository
from salute.integrations.workspace.repositories.storage import DatabaseStorageRepository, StorageRepository


class WorkspaceService:
    @cached_property
    def directory_repository(self) -> DirectoryRepository:
        return WorkspaceDirectoryRepository(
            credentials_file_path="credentials.json",
            delegated_actor="service-salute@southamptoncityscouts.org.uk",
        )

    @cached_property
    def database_repository(self) -> StorageRepository:
        return DatabaseStorageRepository()

    def sync_workspace_accounts(self) -> None:
        workspace_users = self.directory_repository.list_users()

        # Synchronise or add each user account
        for workspace_user in tqdm(workspace_users, "Synchronising users"):
            account, _ = self.database_repository.update_or_create_account(workspace_user)
            self.database_repository.sync_workspace_account_aliases(workspace_user, account=account)

        # Remove spurious accounts
        if deletion_result := self.database_repository.delete_spurious_workspace_accounts(workspace_users):
            print(f"Deleted workspace accounts that no longer exist: {deletion_result.deleted_accounts}")
