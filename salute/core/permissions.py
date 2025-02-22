# mypy: disable-error-code="no-untyped-call"
import rules

from salute.core.predicates import user_has_related_person

# Hierarchy
rules.add_perm("district.view", user_has_related_person)

rules.add_perm("group.list", user_has_related_person)
rules.add_perm("group.view", user_has_related_person)

rules.add_perm("section.list", user_has_related_person)
rules.add_perm("section.view", user_has_related_person)

rules.add_perm("section_type.list", user_has_related_person)
