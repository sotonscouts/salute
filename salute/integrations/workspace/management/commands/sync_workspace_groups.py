from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from google.oauth2 import service_account
from googleapiclient.discovery import build
from tqdm import tqdm  # type: ignore[import-untyped]

from salute.integrations.workspace.models import WorkspaceAccount, WorkspaceGroup

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/admin.directory.group",
    "https://www.googleapis.com/auth/apps.groups.settings",
    "https://www.googleapis.com/auth/gmail.settings.basic",
    "https://www.googleapis.com/auth/gmail.settings.sharing",
]

SALUTE_MANAGED_GROUP_EMAIL_SUFFIX = "@southamptoncityscouts.org.uk"
SALUTE_MANAGED_GROUP_DESCRIPTION = (
    "This group is managed by Salute. Please do not modify it directly in Google Workspace."
)


def get_group_settings(*, can_receive_external_email: bool, can_members_send_as: bool) -> dict[str, Any]:
    return {
        "whoCanJoin": "CAN_REQUEST_TO_JOIN",  # Non members can request an invitation to join.
        "whoCanViewMembership": "ALL_IN_DOMAIN_CAN_VIEW",
        "whoCanViewGroup": "ALL_IN_DOMAIN_CAN_VIEW",
        "allowExternalMembers": "false",  # Users not belonging to the organization are not allowed to become members of this group.  # noqa: E501
        "whoCanPostMessage": "ANYONE_CAN_POST" if can_receive_external_email else "ALL_IN_DOMAIN_CAN_POST",
        "allowWebPosting": "false",  # Members only use Gmail to communicate with the group.
        "primaryLanguage": "en",
        "isArchived": "true",
        "archiveOnly": "false",
        "messageModerationLevel": "MODERATE_NONE",
        "spamModerationLevel": "REJECT",
        # "replyTo": "REPLY_TO_IGNORE",
        "includeCustomFooter": "false",
        "sendMessageDenyNotification": "true",
        "defaultMessageDenyNotificationText": "Sorry, your message was rejected. If you think this is a mistake, please contact digital@southamptoncityscouts.org.uk",  # noqa: E501
        "membersCanPostAsTheGroup": "true" if can_members_send_as else "false",
        "whoCanLeaveGroup": "NONE_CAN_LEAVE",
        "whoCanContactOwner": "ALL_MEMBERS_CAN_CONTACT",
        "favoriteRepliesOnTop": "false",
        "whoCanApproveMembers": "NONE_CAN_APPROVE",  # Due to be deprecated
        "whoCanBanUsers": "NONE",  # Due to be deprecated
        "whoCanModifyMembers": "NONE",  # Due to be deprecated
        "whoCanApproveMessages": "NONE",  # Due to be deprecated
        "whoCanDeleteAnyPost": "NONE",  # Due to be deprecated
        "whoCanDeleteTopics": "NONE",  # Due to be deprecated
        "whoCanLockTopics": "NONE",  # Due to be deprecated
        "whoCanMoveTopicsIn": "NONE",  # Due to be deprecated
        "whoCanMoveTopicsOut": "NONE",  # Due to be deprecated
        "whoCanPostAnnouncements": "NONE",  # Due to be deprecated
        "whoCanHideAbuse": "NONE",  # Due to be deprecated
        "whoCanMakeTopicsSticky": "NONE",  # Due to be deprecated
        "whoCanModerateMembers": "NONE",  # Due to be deprecated
        "whoCanModerateContent": "NONE",  # Due to be deprecated
        "whoCanAssistContent": "NONE",  # Due to be deprecated
        "customRolesEnabledForSettingsToBeMerged": "false",
        "enableCollaborativeInbox": "false",
        "whoCanDiscoverGroup": "ALL_IN_DOMAIN_CAN_DISCOVER",
        "defaultSender": "DEFAULT_SELF",
    }


class Command(BaseCommand):
    help = "Synchronise groups with Google Workspace"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without making actual changes to Google Workspace",
        )
        parser.add_argument(
            "--skip-sendas",
            action="store_true",
            help="Skip syncing sendAs aliases for users",
        )

    def handle(self, *args: str, **options: Any) -> None:
        # Explicitly convert to bool to satisfy the type checker
        dry_run: bool = bool(options.get("dry_run", False))
        skip_sendas: bool = bool(options.get("skip_sendas", False))

        if dry_run:
            self.stdout.write(
                self.style.WARNING("Running in dry run mode - no changes will be made to Google Workspace")
            )

        credentials = service_account.Credentials.from_service_account_file("credentials.json", scopes=SCOPES)  # type: ignore[no-untyped-call]
        delegated_credentials = credentials.with_subject("dan.trickey@southamptoncityscouts.org.uk")
        directory_service = build("admin", "directory_v1", credentials=delegated_credentials)
        group_settings_service = build("groupssettings", "v1", credentials=delegated_credentials)
        gmail_service = build("gmail", "v1", credentials=delegated_credentials)

        # Sync groups
        groups_to_sync = WorkspaceGroup.objects.filter(system_mailing_group__isnull=False).select_related(
            "system_mailing_group"
        )

        for group in tqdm(groups_to_sync, "Syncing Groups"):
            self.sync_system_mailing_group(group, directory_service, group_settings_service, dry_run=dry_run)

        # Sync sendAs aliases for users
        if not skip_sendas:
            self.sync_user_sendas_aliases(directory_service, gmail_service, dry_run=dry_run)

    def sync_system_mailing_group(
        self, group: WorkspaceGroup, directory_service: Any, group_settings_service: Any, *, dry_run: bool = False
    ) -> None:
        self.sync_basic_group_details(group, directory_service, dry_run=dry_run)
        self.sync_group_settings(group, group_settings_service, dry_run=dry_run)
        self.sync_group_members(group, directory_service, dry_run=dry_run)

    def sync_basic_group_details(self, group: WorkspaceGroup, directory_service: Any, *, dry_run: bool = False) -> None:
        """
        Sync the basic details of a Google Workspace group to match Salute's configuration.

        Checks and updates the group's name, description, and email address if needed.
        """
        assert group.system_mailing_group is not None
        expected_address = group.system_mailing_group.name + SALUTE_MANAGED_GROUP_EMAIL_SUFFIX
        expected_name = group.system_mailing_group.display_name
        expected_description = SALUTE_MANAGED_GROUP_DESCRIPTION

        # Get the group details from Google Workspace
        group_details = directory_service.groups().get(groupKey=group.google_id).execute()

        # Check for mismatches
        mismatches = []
        if group_details.get("name") != expected_name:
            mismatches.append(f"name: '{group_details.get('name', '')}' != '{expected_name}'")

        if group_details.get("description") != expected_description:
            mismatches.append("description does not match expected value")

        if group_details.get("email") != expected_address:
            mismatches.append(f"email: '{group_details.get('email', '')}' != '{expected_address}'")

        # Update group if needed
        if mismatches:
            print(f"Updating Google Workspace group for '{group.name}'. Mismatches found: {', '.join(mismatches)}")

            if not dry_run:
                directory_service.groups().update(
                    groupKey=group.google_id,
                    body={
                        "name": expected_name,
                        "description": expected_description,
                        "email": expected_address,
                    },
                ).execute()

                group.name = expected_name
                group.description = expected_description
                group.email = expected_address
                group.save()
            else:
                print(f"  [DRY RUN] Would update group: {group.email} with new details")

    def sync_group_settings(self, group: WorkspaceGroup, group_settings_service: Any, *, dry_run: bool = False) -> None:
        """
        Sync the settings of a Google Workspace group to match Salute's configuration.

        Updates the group's settings based on Salute's configuration.

        Args:
            group: The WorkspaceGroup object to sync.
            service: The Google Workspace service object.
        """
        assert group.system_mailing_group is not None
        settings = get_group_settings(
            can_receive_external_email=group.system_mailing_group.can_receive_external_email,
            can_members_send_as=group.system_mailing_group.can_members_send_as,
        )

        if dry_run:
            print(f"  [DRY RUN] Would update settings for group: {group.email}")
        else:
            group_settings_service.groups().update(
                groupUniqueId=group.system_mailing_group.name + SALUTE_MANAGED_GROUP_EMAIL_SUFFIX,
                body=settings,
            ).execute()

    def sync_group_members(self, group: WorkspaceGroup, directory_service: Any, *, dry_run: bool = False) -> None:
        """
        Sync the members of a Google Workspace group to match Salute's configuration.

        Updates the group's members based on Salute's configuration, ensuring all members
        have the MEMBER role (not OWNER or MANAGER).
        """
        assert group.system_mailing_group is not None

        # Get the current members from Google Workspace
        current_members_response = directory_service.members().list(groupKey=group.google_id).execute()
        current_members = current_members_response.get("members", [])

        # Get the expected members from Salute's SystemMailingGroup
        expected_members = group.system_mailing_group.members.filter(workspace_account__isnull=False).select_related(
            "workspace_account"
        )

        # Create dictionaries for member data
        current_member_data = {
            member.get("id"): {"email": member.get("email"), "role": member.get("role")}
            for member in current_members
            if member.get("id")
        }

        expected_member_data = {
            person.workspace_account.google_id: person.workspace_account.primary_email for person in expected_members
        }

        # Calculate set differences using dictionary views
        members_to_remove = current_member_data.keys() - expected_member_data.keys()
        members_to_add = expected_member_data.keys() - current_member_data.keys()
        members_to_update = current_member_data.keys() & expected_member_data.keys()

        # Remove members not in expected set
        for member_id in members_to_remove:
            member_email = current_member_data[member_id]["email"]
            print(f"Removing member {member_email} from {group.email}")

            if not dry_run:
                directory_service.members().delete(groupKey=group.google_id, memberKey=member_id).execute()
            else:
                print(f"  [DRY RUN] Would remove member: {member_email}")

        # Update role for existing members if needed
        for member_id in members_to_update:
            if current_member_data[member_id]["role"] != "MEMBER":
                member_email = current_member_data[member_id]["email"]
                current_role = current_member_data[member_id]["role"]
                print(f"Updating role for {member_email} in {group.email} from {current_role} to MEMBER")

                if not dry_run:
                    directory_service.members().update(
                        groupKey=group.google_id, memberKey=member_id, body={"role": "MEMBER"}
                    ).execute()
                else:
                    print(f"  [DRY RUN] Would update role for {member_email} from {current_role} to MEMBER")

        # Add new members
        for google_id in members_to_add:
            email = expected_member_data[google_id]
            print(f"Adding member {email} to {group.email}")

            if not dry_run:
                directory_service.members().insert(
                    groupKey=group.google_id, body={"id": google_id, "role": "MEMBER"}
                ).execute()
            else:
                print(f"  [DRY RUN] Would add member: {email}")

    def sync_user_sendas_aliases(self, directory_service: Any, gmail_service: Any, *, dry_run: bool = False) -> None:
        """
        Sync sendAs aliases for workspace accounts by authenticating as each user.

        For each WorkspaceAccount:
        1. List the sendAs aliases
        2. For any aliases that are groups linked to a SystemMailingGroup:
           - If can_members_send_as=False, remove the sendAs alias regardless of membership
           - If can_members_send_as=True and the user is a member, ensure the alias exists with correct name
           - If the user is not a member, remove the sendAs alias
        3. If a user is a member of a group with can_members_send_as=True, ensure they have the sendAs alias
        4. Remove sendAs aliases if the user is no longer a group member
        """
        self.stdout.write("Syncing sendAs aliases for users...")

        # Get all workspace accounts
        workspace_accounts = WorkspaceAccount.objects.filter(person__isnull=False).select_related("person")

        # Build a lookup of groups by email
        groups_by_email: dict[str, WorkspaceGroup] = {}
        groups_with_sendas_enabled: set[str] = set()  # Set of group emails that have can_members_send_as=True

        for group in WorkspaceGroup.objects.filter(system_mailing_group__isnull=False).select_related(
            "system_mailing_group"
        ):
            groups_by_email[group.email] = group
            if group.system_mailing_group and group.system_mailing_group.can_members_send_as:
                groups_with_sendas_enabled.add(group.email)

        # For efficient lookups, pre-fetch group memberships, but only for groups with sendAs enabled
        group_memberships: dict[str, set[str]] = {}  # group_email -> set of user_google_ids

        for group in tqdm(groups_by_email.values(), "Fetching group memberships"):
            if group.email not in groups_with_sendas_enabled:
                continue

            members_response = directory_service.members().list(groupKey=group.google_id).execute()
            members = members_response.get("members", [])

            group_memberships[group.email] = {member.get("id") for member in members if member.get("id")}

        # Process each workspace account
        for account in tqdm(workspace_accounts, "Syncing user sendAs aliases"):
            try:
                # Create credentials specific to this user
                user_credentials = service_account.Credentials.from_service_account_file(  # type: ignore[no-untyped-call]
                    "credentials.json", scopes=SCOPES
                ).with_subject(account.primary_email)

                # Create a Gmail service as this user
                user_gmail_service = build("gmail", "v1", credentials=user_credentials)

                # Now use "me" since we're authenticated as the actual user
                sendas_response = user_gmail_service.users().settings().sendAs().list(userId="me").execute()
                sendas_list = sendas_response.get("sendAs", [])

                current_sendas_emails = {alias.get("sendAsEmail") for alias in sendas_list}

                # Track which group aliases the user should have
                should_have_aliases = set()

                # Check each alias to see if it's a group
                for alias in sendas_list:
                    alias_email = alias.get("sendAsEmail")

                    if alias_email in groups_by_email:
                        group = groups_by_email[alias_email]
                        assert group.system_mailing_group is not None

                        # Check if the group allows send-as
                        if alias_email not in groups_with_sendas_enabled:
                            # Group doesn't allow send-as, so remove this alias
                            if not dry_run:
                                print(
                                    f"Removing sendAs alias {alias_email} from {account.primary_email} (send-as disabled for group)"  # noqa: E501
                                )
                                user_gmail_service.users().settings().sendAs().delete(
                                    userId="me",
                                    sendAsEmail=alias_email,
                                ).execute()
                            else:
                                print(
                                    f"  [DRY RUN] Would remove sendAs alias {alias_email} from {account.primary_email} (send-as disabled for group)"  # noqa: E501
                                )
                            continue

                        # Group allows send-as, check if user is a member
                        is_member = account.google_id in group_memberships.get(alias_email, set())

                        if is_member:
                            # User should have this alias - check if display name is correct
                            should_have_aliases.add(alias_email)

                            expected_display_name = group.system_mailing_group.display_name
                            current_display_name = alias.get("displayName", "")

                            if current_display_name != expected_display_name:
                                if not dry_run:
                                    print(f"Updating sendAs alias {alias_email} for {account.primary_email}")
                                    user_gmail_service.users().settings().sendAs().update(
                                        userId="me",
                                        sendAsEmail=alias_email,
                                        body={
                                            "displayName": expected_display_name,
                                            "isDefault": False,
                                        },
                                    ).execute()
                                else:
                                    print(
                                        f"  [DRY RUN] Would update sendAs alias {alias_email} for {account.primary_email}"  # noqa: E501
                                    )
                        else:
                            # User is not a member, remove this alias
                            if not dry_run:
                                print(
                                    f"Removing sendAs alias {alias_email} from {account.primary_email} (not a member of group)"  # noqa: E501
                                )
                                user_gmail_service.users().settings().sendAs().delete(
                                    userId="me",
                                    sendAsEmail=alias_email,
                                ).execute()
                            else:
                                print(
                                    f"  [DRY RUN] Would remove sendAs alias {alias_email} from {account.primary_email} (not a member of group)"  # noqa: E501
                                )

                # Find groups the user is a member of but doesn't have sendAs aliases for
                for group_email in groups_with_sendas_enabled:
                    member_ids = group_memberships.get(group_email, set())
                    if (
                        account.google_id in member_ids
                        and group_email not in current_sendas_emails
                        and group_email != account.primary_email
                    ):
                        group = groups_by_email[group_email]
                        assert group.system_mailing_group is not None
                        if not dry_run:
                            print(f"Adding sendAs alias {group_email} for {account.primary_email}")
                            try:
                                user_gmail_service.users().settings().sendAs().create(
                                    userId="me",
                                    body={
                                        "sendAsEmail": group_email,
                                        "displayName": group.system_mailing_group.display_name,
                                        "isDefault": False,
                                        "treatAsAlias": True,
                                    },
                                ).execute()
                            except Exception as create_error:  # noqa: BLE001
                                self.stderr.write(f"  Error adding sendAs alias {group_email}: {str(create_error)}")
                        else:
                            print(f"  [DRY RUN] Would add sendAs alias {group_email} for {account.primary_email}")
            except Exception as e:  # noqa: BLE001
                self.stderr.write(f"Error syncing sendAs aliases for {account.primary_email}: {str(e)}")
