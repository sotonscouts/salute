import factory

from salute.people.factories import PersonFactory
from salute.wifi.models import WifiAccount, WifiAccountGroup


class WifiAccountGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WifiAccountGroup

    name = factory.Faker("company")
    slug = factory.Faker("slug")
    description = factory.Faker("sentence")
    is_default = factory.Faker("boolean")


class WifiAccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WifiAccount

    person = factory.SubFactory(PersonFactory)
    group = factory.SubFactory(WifiAccountGroupFactory)
    username = factory.Faker("user_name")
    password = factory.Faker("password")
    is_active = True
