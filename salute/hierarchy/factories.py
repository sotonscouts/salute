import uuid
import zoneinfo

import factory

from .constants import DISTRICT_SECTION_TYPES, GROUP_SECTION_TYPES, GroupType, Weekday
from .models import District, Group, Locality, Section, TSAUnit


class TSAUnitFactory(factory.django.DjangoModelFactory):
    unit_name = factory.Faker("company")
    shortcode = factory.Faker("bothify", text="#######??")
    tsa_id = factory.LazyFunction(uuid.uuid4)
    tsa_last_modified = factory.Faker("past_datetime", tzinfo=zoneinfo.ZoneInfo("Europe/London"))

    class Meta:
        model = TSAUnit


class DistrictFactory(TSAUnitFactory):
    class Meta:
        model = District


class LocalityFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("city")
    class Meta:
        model = Locality


class GroupFactory(TSAUnitFactory):
    district = factory.SubFactory(DistrictFactory)
    locality = factory.SubFactory(LocalityFactory)
    group_type = factory.Iterator([choice[0] for choice in GroupType.choices])
    charity_number = factory.Sequence(lambda n: 100000 + n)
    local_unit_number = factory.Sequence(lambda n: n + 1)
    location_name = factory.Faker("city")

    class Meta:
        model = Group


class DistrictSectionFactory(TSAUnitFactory):
    section_type = factory.Iterator(DISTRICT_SECTION_TYPES)
    usual_weekday = factory.Iterator(Weekday)
    district = factory.SubFactory(DistrictFactory)
    nickname = factory.Faker("company")

    group = None

    class Meta:
        model = Section


class GroupSectionFactory(TSAUnitFactory):
    section_type = factory.Iterator(GROUP_SECTION_TYPES)
    usual_weekday = factory.Iterator(Weekday)
    group = factory.SubFactory(GroupFactory)
    district = None

    class Meta:
        model = Section
