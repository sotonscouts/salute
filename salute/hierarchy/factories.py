import factory

from salute.integrations.tsa.models import TSAObject

from .constants import DISTRICT_SECTION_TYPES, GROUP_SECTION_TYPES, GroupType, SectionType
from .models import District, Group, Section


class TSAObjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TSAObject
        abstract = True


class TSAUnitFactory(TSAObjectFactory):
    unit_name = factory.Faker("company")
    shortcode = factory.Faker("bothify", text="#######??")

    class Meta:
        model = District
        abstract = True


class DistrictFactory(TSAUnitFactory):
    class Meta:
        model = District


class GroupFactory(TSAUnitFactory):
    district = factory.SubFactory(DistrictFactory)
    group_type = factory.Iterator([choice[0] for choice in GroupType.choices])
    charity_number = factory.Sequence(lambda n: 100000 + n)
    local_unit_number = factory.Sequence(lambda n: n + 1)
    location_name = factory.Faker("city")

    class Meta:
        model = Group


class SectionFactory(TSAUnitFactory):
    district = factory.Maybe(
        lambda o: o.section_type in DISTRICT_SECTION_TYPES,
        yes_declaration=factory.SubFactory(DistrictFactory),
        no_declaration=None,
    )
    group = factory.Maybe(
        lambda o: o.section_type in GROUP_SECTION_TYPES,
        yes_declaration=factory.SubFactory(GroupFactory),
        no_declaration=None,
    )
    section_type = factory.Iterator([choice[0] for choice in SectionType.choices])

    class Meta:
        model = Section
