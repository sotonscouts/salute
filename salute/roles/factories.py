import zoneinfo

import factory

from .models import Accreditation, AccreditationType, Role, RoleStatus, RoleType, Team, TeamType


class TeamTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TeamType

    name = factory.Faker("word")
    tsa_id = factory.Faker("uuid4")


class TeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Team

    team_type = factory.SubFactory(TeamTypeFactory)

    district = None
    group = None
    section = None
    parent_team = None

    allow_sub_team = factory.Faker("boolean")
    inherit_permissions = factory.Faker("boolean")


class DistrictTeamFactory(TeamFactory):
    district = factory.SubFactory("salute.hierarchy.factories.DistrictFactory")


class GroupTeamFactory(TeamFactory):
    group = factory.SubFactory("salute.hierarchy.factories.GroupFactory")


class GroupSectionTeamFactory(TeamFactory):
    section = factory.SubFactory("salute.hierarchy.factories.GroupSectionFactory")


class DistrictSectionTeamFactory(TeamFactory):
    section = factory.SubFactory("salute.hierarchy.factories.DistrictSectionFactory")


class DistrictSubTeamFactory(TeamFactory):
    parent_team = factory.SubFactory(DistrictTeamFactory)


class GroupSubTeamFactory(TeamFactory):
    parent_team = factory.SubFactory(GroupTeamFactory)


class RoleTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RoleType

    name = factory.Faker("word")


class RoleStatusFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RoleStatus

    name = factory.Faker("word")


class RoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Role

    team = factory.SubFactory(DistrictTeamFactory)
    person = factory.SubFactory("salute.people.factories.PersonFactory")
    tsa_id = factory.Faker("uuid4")

    role_type = factory.SubFactory(RoleTypeFactory)
    status = factory.SubFactory(RoleStatusFactory)


class AccreditationTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AccreditationType

    name = factory.Faker("word")
    tsa_id = factory.Faker("uuid4")


class AccreditationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Accreditation

    accreditation_type = factory.SubFactory(AccreditationTypeFactory)
    person = factory.SubFactory("salute.people.factories.PersonFactory")
    team = factory.SubFactory(DistrictTeamFactory)
    tsa_id = factory.Faker("uuid4")

    status = "Active"
    expires_at = factory.Faker("future_datetime", tzinfo=zoneinfo.ZoneInfo("Europe/London"))
    granted_at = factory.Faker("past_datetime", tzinfo=zoneinfo.ZoneInfo("Europe/London"))
