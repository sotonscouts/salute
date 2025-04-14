from typing import Any

from django.core.management.base import BaseCommand
from google.oauth2 import service_account
from googleapiclient.discovery import build
from tqdm import tqdm

from salute.integrations.workspace.models import (
    WorkspaceAccount,
    WorkspaceAccountAlias,
    WorkspaceGroup,
    WorkspaceGroupAlias,
)
from salute.people.models import Person

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/admin.directory.user",
    "https://www.googleapis.com/auth/admin.directory.group",
]
DISABLED_ACCOUNT_ORG_UNIT_PATH = "/Disabled Accounts"
SERVICE_ACCOUNT_ORG_UNIT_PATH = "/Service Accounts"


class Command(BaseCommand):
    help = "Synchronise with Google Workspace"

    # def add_arguments(self, parser):
    #     parser.add_argument("poll_ids", nargs="+", type=int)

    def handle(self, *args: str, **options: str) -> None:
        credentials = service_account.Credentials.from_service_account_file("credentials.json", scopes=SCOPES)  # type: ignore[no-untyped-call]
        delegated_credentials = credentials.with_subject("dan.trickey@southamptoncityscouts.org.uk")
        service = build("admin", "directory_v1", credentials=delegated_credentials)

        self.sync_workspace_users(service)

        for workspace_account in WorkspaceAccount.objects.exclude(
            org_unit_path__startswith=SERVICE_ACCOUNT_ORG_UNIT_PATH
        ):
            self.audit_workspace_user(workspace_account)

        self.sync_workspace_groups(service)

    def sync_workspace_users(self, directory_service: Any) -> None:
        # Initial request
        results = directory_service.users().list(customer="my_customer", maxResults=100).execute()
        users = results.get("users", [])

        # Iterate through pages
        while "nextPageToken" in results:
            page_token = results["nextPageToken"]
            results = (
                directory_service.users().list(customer="my_customer", pageToken=page_token, maxResults=100).execute()
            )
            users.extend(results.get("users", []))

        for workspace_user in tqdm(users, "Syncing Workspace Users"):
            account, _ = WorkspaceAccount.objects.update_or_create(
                {
                    "primary_email": workspace_user["primaryEmail"],
                    "given_name": workspace_user["name"]["givenName"],
                    "family_name": workspace_user["name"]["familyName"],
                    # Editable Flags
                    "archived": workspace_user["archived"],
                    "change_password_at_next_login": workspace_user["changePasswordAtNextLogin"],
                    "suspended": workspace_user["suspended"],
                    # Read Only Attributes
                    "agreed_to_terms": workspace_user["agreedToTerms"],
                    "external_ids": workspace_user.get("externalIds", []),
                    "is_admin": workspace_user["isAdmin"],
                    "is_delegated_admin": workspace_user["isDelegatedAdmin"],
                    "is_enforced_in_2sv": workspace_user["isEnforcedIn2Sv"],
                    "is_enrolled_in_2sv": workspace_user["isEnrolledIn2Sv"],
                    "org_unit_path": workspace_user["orgUnitPath"],
                    # Security
                    "has_recovery_email": workspace_user.get("recoveryEmail") is not None,
                    "has_recovery_phone": workspace_user.get("recoveryPhone") is not None,
                    # Timestamps
                    "creation_time": workspace_user["creationTime"],
                    "last_login_time": workspace_user.get("lastLoginTime", None),
                },
                google_id=int(workspace_user["id"]),
            )

            # Add alias
            aliases = set(workspace_user.get("aliases", []))
            for alias in aliases:
                WorkspaceAccountAlias.objects.update_or_create({"account": account}, address=alias)
            if sprurious_aliases := WorkspaceAccountAlias.objects.filter(account=account).exclude(address__in=aliases):
                print(f"Deleting spurious aliases: {sprurious_aliases}")
                sprurious_aliases.delete()

        # Remove deleted accounts
        if spurious_workspace_accounts := WorkspaceAccount.objects.exclude(
            google_id__in=[workspace_user["id"] for workspace_user in users]
        ):
            print(f"Deleting workspace accounts that no longer exist: {spurious_workspace_accounts}")
            spurious_workspace_accounts.delete()

    def audit_workspace_user(self, account: WorkspaceAccount) -> None:
        # Attempt to link to user
        external_ids_by_type = {external_id["type"]: external_id["value"] for external_id in account.external_ids}
        membership_id = external_ids_by_type.get("organization")
        if membership_id is None:
            if not (account.suspended and account.org_unit_path == DISABLED_ACCOUNT_ORG_UNIT_PATH):
                print(f"Missing membership ID for {account} ({account.org_unit_path})")
            return

        mem_id = int(membership_id)

        if account.person is None:
            # Unlinked
            if account.suspended and account.org_unit_path == DISABLED_ACCOUNT_ORG_UNIT_PATH:
                # Account suspended. Ignore.
                return

            if person := Person.objects.filter(membership_number=mem_id).first():
                print(f"Link {account} to {person}")
                account.person = person
                account.save(update_fields=["person"])
            else:
                print(
                    f"Unable to find matching membership ID for {account}. "
                    f"Please deactivate account and move to {DISABLED_ACCOUNT_ORG_UNIT_PATH!r}"
                )
                return
        else:
            if account.person.membership_number != mem_id:
                print(f"Membership ID for {account} seems incorrect, account is linked to {account.person}")

        if account.person.is_suspended:
            print(f"Warning: {account.person} is a suspended volunteer but has an active account: {account}")

        # TODO: Identify suspended accounts for existing members
        # TODO: Identify suspended members with active accounts
        # TODO: Move print statements into an audit function, it's not the same as sync.

    def sync_workspace_groups(self, directory_service: Any) -> None:
        # Initial request
        results = directory_service.groups().list(customer="my_customer", maxResults=100).execute()
        groups = results.get("groups", [])

        # Iterate through pages
        while "nextPageToken" in results:
            page_token = results["nextPageToken"]
            results = (
                directory_service.groups().list(customer="my_customer", pageToken=page_token, maxResults=100).execute()
            )
            groups.extend(results.get("groups", []))

        for workspace_group in tqdm(groups, "Syncing Workspace Groups"):
            group, _ = WorkspaceGroup.objects.update_or_create(
                {
                    "email": workspace_group["email"],
                    "name": workspace_group["name"],
                    "description": workspace_group["description"],
                },
                google_id=workspace_group["id"],
            )

            # Add alias
            aliases = set(workspace_group.get("aliases", []))
            for alias in aliases:
                WorkspaceGroupAlias.objects.update_or_create({"group": group}, address=alias)
            if sprurious_aliases := WorkspaceGroupAlias.objects.filter(group=group).exclude(address__in=aliases):
                print(f"Deleting spurious aliases: {sprurious_aliases}")
                sprurious_aliases.delete()

        # Remove deleted groups
        if spurious_workspace_groups := WorkspaceGroup.objects.exclude(
            google_id__in=[workspace_group["id"] for workspace_group in groups]
        ):
            print(f"Deleting workspace groups that no longer exist: {spurious_workspace_groups}")
            spurious_workspace_groups.delete()
