import factory

from salute.mailing_groups.models import SystemMailingGroup


class SystemMailingGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SystemMailingGroup

    name = factory.Faker("company")
    display_name = factory.Faker("company")
    short_name = factory.Faker("company")
    composite_key = factory.Faker("uuid4")
    config = {}  # type: ignore[var-annotated]
