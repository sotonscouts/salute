# mypy: disable-error-code="no-untyped-call"
import rules

from salute.core.predicates import (
    can_list_workspace_accounts,
    can_view_accreditation,
    can_view_group_summary_data,
    can_view_person,
    can_view_person_pii,
    can_view_role,
    can_view_section_summary_data,
    can_view_site_tenure_type,
    can_view_team_person_count,
    can_view_workspace_account,
    can_view_workspace_account_pii,
    user_has_related_person,
)

# Hierarchy
rules.add_perm("district.view", user_has_related_person)
rules.add_perm("district.view_young_person_count", user_has_related_person)

rules.add_perm("group.list", user_has_related_person)
rules.add_perm("group.view", user_has_related_person)
rules.add_perm("group.view_young_person_count", can_view_group_summary_data)

rules.add_perm("section.list", user_has_related_person)
rules.add_perm("section.view", user_has_related_person)
rules.add_perm("section.view_young_person_count", can_view_section_summary_data)
rules.add_perm("section.view_census_returns", can_view_section_summary_data)

rules.add_perm("section_type.list", user_has_related_person)

# People
rules.add_perm("person.list", user_has_related_person)
rules.add_perm("person.view", can_view_person)
rules.add_perm("person.view_pii", can_view_person_pii)

# Roles
rules.add_perm("accreditation_type.list", user_has_related_person)
rules.add_perm("accreditation_type.view", user_has_related_person)

rules.add_perm("accreditation.list", user_has_related_person)
rules.add_perm("accreditation.view", can_view_accreditation)

rules.add_perm("role.list", user_has_related_person)
rules.add_perm("role.view", can_view_role)

rules.add_perm("role_status.list", user_has_related_person)

rules.add_perm("role_type.list", user_has_related_person)
rules.add_perm("role_type.view", user_has_related_person)

rules.add_perm("team_type.list", user_has_related_person)
rules.add_perm("team_type.view", user_has_related_person)

rules.add_perm("team.list", user_has_related_person)
rules.add_perm("team.view", user_has_related_person)
rules.add_perm("team.view_person_count", can_view_team_person_count)

# Locations
rules.add_perm("site.list", user_has_related_person)
rules.add_perm("site.view", user_has_related_person)
rules.add_perm("site.view_site_tenure_type", can_view_site_tenure_type)

# Mailing Groups
rules.add_perm("system_mailing_group.list", user_has_related_person)
rules.add_perm("system_mailing_group.view", user_has_related_person)

# Workspace
rules.add_perm("workspace_account.list", can_list_workspace_accounts)
rules.add_perm("workspace_account.view", can_view_workspace_account)
rules.add_perm("workspace_account.view_pii", can_view_workspace_account_pii)
