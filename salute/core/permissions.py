# mypy: disable-error-code="no-untyped-call"
import rules

from salute.core.predicates import can_view_person, can_view_person_pii, user_has_related_person

# Hierarchy
rules.add_perm("district.view", user_has_related_person)

rules.add_perm("group.list", user_has_related_person)
rules.add_perm("group.view", user_has_related_person)

rules.add_perm("section.list", user_has_related_person)
rules.add_perm("section.view", user_has_related_person)

rules.add_perm("section_type.list", user_has_related_person)

# People
rules.add_perm("person.list", user_has_related_person)
rules.add_perm("person.view", can_view_person)
rules.add_perm("person.view_pii", can_view_person_pii)

# Roles
rules.add_perm("accreditation_type.list", user_has_related_person)
rules.add_perm("accreditation_type.view", user_has_related_person)

rules.add_perm("role_status.list", user_has_related_person)

rules.add_perm("role_type.list", user_has_related_person)
rules.add_perm("role_type.view", user_has_related_person)

rules.add_perm("team_type.list", user_has_related_person)
rules.add_perm("team_type.view", user_has_related_person)
