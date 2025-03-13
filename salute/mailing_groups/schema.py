from __future__ import annotations

import operator
from functools import reduce
from typing import Literal
from uuid import UUID

from django.db.models import Q, QuerySet
from pydantic import BaseModel

from salute.people.models import Person
from salute.roles.models import Role, Team


class BaseUnitRef(BaseModel):
    type: str
    unit_id: UUID

    def as_query_filters(self) -> dict[str, UUID]:
        return {self.type: self.unit_id}

    def as_parent_query_filters(self) -> dict[str, UUID]:
        return {f"parent_team__{self.type}": self.unit_id}


class DistrictUnitRef(BaseUnitRef):
    type: Literal["district"] = "district"


class GroupUnitRef(BaseUnitRef):
    type: Literal["group"] = "group"
    unit_id: UUID


class SectionUnitRef(BaseUnitRef):
    type: Literal["section"] = "section"
    unit_id: UUID


class MailGroupConfig(BaseModel):
    """
    Filters for a mail group configuration to get members based on roles.
    """

    role_type_id: UUID | None = None
    team_type_id: UUID | None = None
    include_sub_teams: bool = False
    is_all_members_list: bool = False
    units: list[DistrictUnitRef | GroupUnitRef | SectionUnitRef] | None = (
        None  # = Field(discriminator='type', default=None)
    )

    def get_roles(self) -> QuerySet[Role]:
        teams = Team.objects.all()
        if self.team_type_id is not None:
            team_type_filter = Q(team_type_id=self.team_type_id)
            if self.include_sub_teams:
                team_type_filter = team_type_filter | Q(parent_team__team_type_id=self.team_type_id)

            teams = teams.filter(team_type_filter)

        if self.units is not None:
            teams = teams.filter(
                reduce(
                    operator.or_,
                    [Q(**unit.as_query_filters()) for unit in self.units]
                    + [Q(**unit.as_parent_query_filters()) for unit in self.units],
                )
            )

        if self.is_all_members_list:
            teams = teams.exclude(team_type__included_in_all_members=False)

        roles = Role.objects.filter(team__in=teams)

        if self.role_type_id is not None:
            roles = roles.filter(role_type_id=self.role_type_id)

        return roles

    def get_members(self) -> QuerySet[Person]:
        roles = self.get_roles()
        return Person.objects.filter(id__in=roles.values("person"))
