import factory

from salute.hierarchy.factories import GroupSectionFactory
from salute.integrations.osm.models import OSMSectionHeadcountRecord


class OSMSectionHeadcountRecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OSMSectionHeadcountRecord

    section = factory.SubFactory(GroupSectionFactory)
    date = factory.Faker("date_this_decade")
    young_person_count = factory.Faker("random_int", min=0, max=100)
    adult_count = factory.Faker("random_int", min=0, max=100)
