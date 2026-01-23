import factory

from salute.integrations.waiting_list.models import WaitingListEntry


class WaitingListEntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WaitingListEntry

    external_id = factory.Faker("uuid4")
    date_of_birth = factory.Faker("date_of_birth")
    postcode = factory.Faker("postcode")
    joined_waiting_list_at = factory.Faker("date_time")
    successfully_transferred = factory.Faker("boolean")
