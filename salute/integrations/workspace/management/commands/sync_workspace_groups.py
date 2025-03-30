from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from google.oauth2 import service_account
from googleapiclient.discovery import build
from tqdm import tqdm  # type: ignore[import-untyped]

from salute.integrations.workspace.models import WorkspaceGroup

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/admin.directory.group",
    "https://www.googleapis.com/auth/apps.groups.settings",
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

    def handle(self, *args: str, **options: Any) -> None:
        # Explicitly convert to bool to satisfy the type checker
        dry_run = bool(options.get("dry_run", False))

        if dry_run:
            self.stdout.write(
                self.style.WARNING("Running in dry run mode - no changes will be made to Google Workspace")
            )

        credentials = service_account.Credentials.from_service_account_file("credentials.json", scopes=SCOPES)  # type: ignore[no-untyped-call]
        delegated_credentials = credentials.with_subject("dan.trickey@southamptoncityscouts.org.uk")
        directory_service = build("admin", "directory_v1", credentials=delegated_credentials)
        group_settings_service = build("groupssettings", "v1", credentials=delegated_credentials)

        groups_to_sync = WorkspaceGroup.objects.filter(system_mailing_group__isnull=False).select_related(
            "system_mailing_group"
        )

        for group in tqdm(groups_to_sync, "Syncing Groups"):
            self.sync_system_mailing_group(group, directory_service, group_settings_service, dry_run=dry_run)

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
