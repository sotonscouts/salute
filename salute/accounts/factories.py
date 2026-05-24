import zoneinfo

import factory

from salute.accounts.models import ServiceAccount, User


class ServiceAccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ServiceAccount

    description = factory.Faker("sentence", nb_words=3)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Faker("email")
    is_active = True
    last_login = factory.Faker("past_datetime", tzinfo=zoneinfo.ZoneInfo("Europe/London"))
    date_joined = factory.Faker("past_datetime", tzinfo=zoneinfo.ZoneInfo("Europe/London"))
