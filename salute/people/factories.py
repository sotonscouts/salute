import uuid

import factory

from salute.people.models import Person


class PersonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Person

    legal_name = factory.Faker("first_name")
    preferred_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    membership_number = factory.Sequence(lambda n: n + 1)  # Incremental unique numbers
    is_suspended = factory.Faker("boolean")
    primary_email = factory.Maybe(
        factory.Faker("boolean"),
        factory.Faker("email"),
        "",
    )
    default_email = factory.Maybe(
        factory.Faker("boolean"),
        factory.Faker("email"),
        "",
    )
    alternate_email = factory.Maybe(
        factory.Faker("boolean"),
        factory.Faker("email"),
        "",
    )
    phone_number = factory.Faker("phone_number", locale="en_GB")  # Force UK format
    alternate_phone_number = factory.Maybe(
        factory.Faker("boolean"),
        factory.Faker("phone_number", locale="en_GB"),  # Force UK format
        None,
    )

    tsa_id = factory.LazyFunction(uuid.uuid4)
