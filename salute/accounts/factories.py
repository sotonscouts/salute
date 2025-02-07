import zoneinfo

import factory

from salute.accounts.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Faker("email")
    is_active = True
    last_login = factory.Faker("past_datetime", tzinfo=zoneinfo.ZoneInfo("Europe/London"))
    date_joined = factory.Faker("past_datetime", tzinfo=zoneinfo.ZoneInfo("Europe/London"))
