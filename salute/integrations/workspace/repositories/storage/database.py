from salute.integrations.workspace.models import WorkspaceAccount, WorkspaceAccountAlias
from salute.integrations.workspace.repositories.directory._schema import WorkspaceAccountInfo

from .base import (
    DeleteSpuriousAccountsResult,
    SyncAccountAliasesResult,
    UpdateOrCreateAccountResult,
    _WorkspaceAccountInfo,
)


class DatabaseStorageRepository:
    def update_or_create_account(
        self, workspace_user: WorkspaceAccountInfo
    ) -> tuple[WorkspaceAccount, UpdateOrCreateAccountResult]:
        # Serialise the external IDs as JSON
        if workspace_user.external_ids is None:
            external_ids = []
        else:
            external_ids = [eid.model_dump(mode="json") for eid in workspace_user.external_ids]

        # Create or update the workspace account
        account, created = WorkspaceAccount.objects.update_or_create(
            {
                "primary_email": workspace_user.primary_email,
                "given_name": workspace_user.name.given_name,
                "family_name": workspace_user.name.family_name,
                # Editable Flags
                "archived": workspace_user.archived,
                "change_password_at_next_login": workspace_user.change_password_at_next_login,
                "suspended": workspace_user.suspended,
                # Read Only Attributes
                "agreed_to_terms": workspace_user.agreed_to_terms,
                "external_ids": external_ids,
                "is_admin": workspace_user.is_admin,
                "is_delegated_admin": workspace_user.is_delegated_admin,
                "is_enforced_in_2sv": workspace_user.is_enforced_in_2sv,
                "is_enrolled_in_2sv": workspace_user.is_enrolled_in_2sv,
                "org_unit_path": workspace_user.org_unit_path,
                # Security
                "has_recovery_email": workspace_user.recovery_email is not None,
                "has_recovery_phone": workspace_user.recovery_phone is not None,
                # Timestamps
                "creation_time": workspace_user.creation_time,
                "last_login_time": workspace_user.last_login_time,
            },
            google_id=workspace_user.id,
        )

        result = UpdateOrCreateAccountResult(
            google_id=workspace_user.id,
            salute_id=account.id,
            primary_email=workspace_user.primary_email,
            created=created,
        )
        return account, result

    def sync_workspace_account_aliases(
        self,
        workspace_user: WorkspaceAccountInfo,
        *,
        account: WorkspaceAccount | None = None,
    ) -> SyncAccountAliasesResult:
        """
        Sync the aliases of a workspace account.

        Args:
            workspace_user: The workspace user information.
            account: The workspace account to update. If None, it will be fetched from the database.
        """
        if account is None:
            account = WorkspaceAccount.objects.get(google_id=workspace_user.id)

        # Add / update aliases
        aliases = set(workspace_user.aliases)
        for alias in aliases:
            WorkspaceAccountAlias.objects.update_or_create({"account": account}, address=alias)

        # Remove spurious aliases
        if sprurious_aliases := WorkspaceAccountAlias.objects.filter(account=account).exclude(address__in=aliases):
            removed_aliases = list(sprurious_aliases.values_list("address", flat=True))
            print(f"Deleting spurious aliases: {sprurious_aliases}")
            sprurious_aliases.delete()
        else:
            removed_aliases = []

        return SyncAccountAliasesResult(
            google_id=workspace_user.id,
            salute_id=account.id,
            primary_email=workspace_user.primary_email,
            aliases=list(aliases),
            removed_aliases=removed_aliases,
        )

    def delete_spurious_workspace_accounts(
        self, known_users: list[WorkspaceAccountInfo]
    ) -> DeleteSpuriousAccountsResult | None:
        google_ids = [workspace_user.id for workspace_user in known_users]
        spurious_workspace_accounts = WorkspaceAccount.objects.exclude(google_id__in=google_ids)
        accounts_to_delete = [
            _WorkspaceAccountInfo(
                google_id=int(account.google_id), salute_id=account.id, primary_email=account.primary_email
            )
            for account in spurious_workspace_accounts
        ]

        if not accounts_to_delete:
            return None

        spurious_workspace_accounts.delete()
        return DeleteSpuriousAccountsResult(deleted_accounts=accounts_to_delete)
