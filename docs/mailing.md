# Mailing Groups

Salute provides a comprehensive mailing group system that automatically creates and manages email distribution lists based on roles within the organisation. These mailing groups are synchronised with Google Workspace to provide real email addresses that can be used to communicate with various teams and roles.

## System Overview

The mailing group system consists of several components:

1. **SystemMailingGroup** - The core model that defines a mailing group, its configuration, and membership
2. **MailGroupConfig** - A schema that defines how members are selected for a group based on roles and units
3. **WorkspaceGroup** - Represents the Google Workspace group that corresponds to a SystemMailingGroup
4. **Management Commands** - Commands to update mailing groups and sync them with Google Workspace

## SystemMailingGroup

The `SystemMailingGroup` model defines an email distribution list with the following key attributes:

- **name**: The local part of the email address (e.g., "chair" for chair@example.org.uk)
- **display_name**: Human-readable name displayed in email clients (e.g., "District Chair")
- **composite_key**: A unique identifier used to reference the group (e.g., "district_chair")
- **config**: JSON configuration that defines membership rules (stored as a `MailGroupConfig`)
- **can_receive_external_email**: Whether the group can receive emails from outside the organisation
- **can_members_send_as**: Whether members can send emails as this group address
- **fallback_group_composite_key**: Reference to another group to use as fallback if this group has no members
- **always_include_fallback_group**: Whether to always include the fallback group, even if this group has members

## Mailing Group Configuration

Each mailing group is configured using a `MailGroupConfig` schema which defines rules for membership:

- **role_type_id**: Optional - Limits membership to a specific role type (e.g., Chair, Treasurer)
- **team_type_id**: Optional - Limits membership to a specific team type (e.g., Trustees, Leadership)
- **include_sub_teams**: Whether to include members from sub-teams
- **is_all_members_list**: Whether this is an "all members" list (will filter out certain team types)
- **units**: List of units (district, group, section) that this mailing group applies to

The config performs a database query to find all people with roles matching these criteria, and they become the members of the mailing group.

## Creating SystemMailingGroups

SystemMailingGroups are created and updated automatically through the `update_mailing_groups` management command. This command:

1. Fetches the current organisational structure (district, groups, sections, teams)
2. Uses the `MailingGroupUpdater` class to generate appropriate mailing groups at each level
3. Creates or updates `SystemMailingGroup` records using Django's `update_or_create` method
4. Finally calls `update_members()` on each group to populate membership based on the configuration

The creation process follows a hierarchical pattern:

### District Level Creation
- `update_district_top_level_roles()`: Creates groups for district-level leadership roles (Chair, Lead Volunteer, Treasurer)
- `update_district_teams()`: Creates groups for all district teams and their leaders
- `update_explorer_teams()`: Creates groups for Explorer Scout units
- `update_network()`: Creates groups for Scout Network units

### Group Level Creation
- `update_group_top_level_roles()`: Creates groups for each Scout Group's leadership roles
- `update_group_teams()`: Creates groups for teams within each Scout Group
- `update_group_all()`: Creates "all members" groups for each Scout Group
- `update_group_section()`: Creates groups for each section (Beavers, Cubs, Scouts) within each Group

### Example Creation Code
For instance, this is how a district chair mailing group is created:

```python
SystemMailingGroup.objects.update_or_create(
    composite_key="district_chair",
    defaults={
        "name": "chair",
        "display_name": "District Chair",
        "can_receive_external_email": True,
        "can_members_send_as": True,
        "config": {
            "role_type_id": str(RoleType.objects.get(name="Chair").id),
            "team_type_id": str(trustees_team_type.id),
            "units": [{"type": "district", "unit_id": str(district.id)}],
        },
    },
)
```

### Group Naming Conventions
- District roles use simple names like "chair" or "lead"
- Group roles include the group ordinal, e.g., "1st-chair" or "5th-treasurer"
- Section teams include group ordinal, section type, and weekday, e.g., "3rd-beavers-tuesday"
- District teams use their team type's mailing slug, e.g., "activities" or "international"

### Required Data
For the mailing group system to work correctly:
- Teams must have a `mailing_slug` set if they should have email addresses
- Team types need appropriate settings for `has_team_lead` and `has_all_list`
- Sections must have `usual_weekday` set
- Groups need `ordinal` and `location_name` values

## Group Types and Hierarchy

Mailing groups are organised in a hierarchy matching the organisational structure:

### District Level
- Top-level roles (Chair, Lead Volunteer, Treasurer)
- District teams (based on team types with mailing slugs)
- Team leads (for teams with leaders)
- Explorer Scout units and Scout Network
- "All" groups for certain team types

### Group Level
- Top-level roles (Group Lead Volunteer, Chair, Treasurer)
- Group teams (e.g., leadership, trustees)
- Section teams (e.g., Beavers, Cubs, Scouts)
- "All" groups for all members in a group

### Section Level
- Section teams

## Fallback Groups

When a mailing group might not have members (e.g., a section without leaders), a fallback group can be specified. This ensures emails are delivered to someone, even if the primary recipients don't exist.

For example:
- Explorer units may have no leaders at times, so emails fall back to the 14-24 Team Lead

## Google Workspace Integration

Mailing groups are synchronised with Google Workspace through the `sync_workspace_groups` management command:

1. **Group Creation and Updates**: Ensures Google Workspace groups match the configuration in Salute
2. **Membership Sync**: Updates group membership based on the roles in Salute
3. **SendAs Permissions**: Configures which users can send emails as a group address
4. **Group Settings**: Configures settings like who can post to the group, archive settings, etc.

All Google Workspace groups:
- Have addresses ending with @example.org.uk
- Include a standard description indicating they're managed by Salute
- Have permissions set based on their configuration in Salute

## Usage Flow

The system works as follows:

1. The `update_mailing_groups` command creates and updates SystemMailingGroup models based on the current organisational structure
2. Each SystemMailingGroup uses its config to determine who should be members
3. The `sync_workspace_groups` command ensures Google Workspace groups match the Salute configuration
4. Users receive emails sent to these groups based on their roles
5. Users with `can_members_send_as=True` can send emails as the group address

## Maintenance

To update mailing groups after organisational changes:

```bash
# Update mailing groups in Salute
python manage.py update_mailing_groups

# Sync with Google Workspace (use --dry-run to preview changes)
python manage.py sync_workspace_groups
```

## Team Type Configuration for Mailing Groups

Team types require specific configuration to enable email addresses:

### Key Team Type Attributes

The following attributes on the `TeamType` model control how mailing groups are created:

- **mailing_slug**: The local part of the email address used for this team type (e.g., "activities")
- **has_team_lead**: When `True`, creates an additional address for the team lead (e.g., "activities-lead@example.org.uk")
- **has_all_list**: When `True`, creates an "all members" list for teams of this type with sub-teams
- **included_in_all_members**: When `True`, members of this team are included in parent "all members" lists

### Managing Team Type Configurations

Team type configurations can be managed through:

1. **Django Admin Interface**: Navigate to the TeamType section of the admin interface to configure mailing attributes
2. **Database Migrations**: For initial setup or bulk changes, create a data migration that sets these values
3. **Management Shell**: Use Django's shell to programmatically update team types:

```python
# Example: Configure a team type for mailing
from salute.roles.models import TeamType

team_type = TeamType.objects.get(name="Activities")
team_type.mailing_slug = "activities"
team_type.has_team_lead = True
team_type.has_all_list = True
team_type.included_in_all_members = True
team_type.save()
```

After updating team type configurations, run the `update_mailing_groups` command to regenerate the mailing groups with these new settings:

```bash
python manage.py update_mailing_groups
```

### Best Practices for Mailing Slugs

When configuring mailing slugs:

- Keep them short and descriptive (e.g., "activities", "international", "trustees")
- Use lowercase letters without spaces (use hyphens if needed)
- Ensure they are unique across all team types
- Choose slugs that make sense to the recipients (avoid abbreviations when possible)
- For team types that shouldn't have email addresses (like Helpers), leave the mailing_slug empty

## Common Email Patterns

Common email address patterns include:
- District roles: `chair@example.org.uk`, `lead@example.org.uk`
- Group roles: `1st-chair@example.org.uk` (where "1st" is the group ordinal)
- Section teams: `1st-beavers-monday@example.org.uk`
- District teams: `activities@example.org.uk`, `activities-lead@example.org.uk`
- All members: `1st-all@example.org.uk`
