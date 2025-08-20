from __future__ import annotations

from typing import TYPE_CHECKING

import rules

from salute.accounts.models import DistrictUserRoleType
from salute.roles.models import Accreditation

if TYPE_CHECKING:
    from salute.accounts.models import User
    from salute.integrations.workspace.models import WorkspaceAccount
    from salute.people.models import Person
    from salute.roles.models import Role


@rules.predicate
def user_has_related_person(user: User) -> bool:
    return user.person is not None


@rules.predicate
def user_is_person(user: User, person: Person | None) -> bool:
    if person is None:
        return False

    if user.person is None:
        return False

    return user.person == person


@rules.predicate
def user_is_workspace_account(user: User, workspace_account: WorkspaceAccount | None) -> bool:
    if workspace_account is None:
        return False

    return user.person == workspace_account.person


@rules.predicate
def role_belongs_to_person(user: User, role: Role | Accreditation | None) -> bool:
    if role is None:
        return False

    if user.person is None:
        return False

    return user.person == role.person


def has_district_role(role_type: DistrictUserRoleType) -> rules.predicates.Predicate:
    @rules.predicate
    def user_has_district_role(user: User) -> bool:
        return role_type in user.district_role_list

    return user_has_related_person & user_has_district_role


can_list_people = has_district_role(DistrictUserRoleType.MANAGER) | has_district_role(DistrictUserRoleType.ADMIN)
can_view_person_pii = has_district_role(DistrictUserRoleType.ADMIN) | user_is_person
can_view_person = can_list_people | user_is_person

can_list_roles = can_list_people
can_view_role = can_list_people | role_belongs_to_person

can_view_team_person_count = has_district_role(DistrictUserRoleType.MANAGER) | has_district_role(
    DistrictUserRoleType.ADMIN
)

can_list_accreditations = has_district_role(DistrictUserRoleType.MANAGER) | has_district_role(
    DistrictUserRoleType.ADMIN
)
can_view_accreditation = can_list_accreditations | role_belongs_to_person

can_view_site_tenure_type = has_district_role(DistrictUserRoleType.MANAGER) | has_district_role(
    DistrictUserRoleType.ADMIN
)

can_view_group_summary_data = has_district_role(DistrictUserRoleType.MANAGER) | has_district_role(
    DistrictUserRoleType.ADMIN
)

can_view_section_summary_data = has_district_role(DistrictUserRoleType.MANAGER) | has_district_role(
    DistrictUserRoleType.ADMIN
)

can_list_workspace_accounts = has_district_role(DistrictUserRoleType.MANAGER) | has_district_role(
    DistrictUserRoleType.ADMIN
)
can_view_workspace_account = can_list_workspace_accounts | user_is_workspace_account
can_view_workspace_account_pii = has_district_role(DistrictUserRoleType.ADMIN) | user_is_workspace_account
