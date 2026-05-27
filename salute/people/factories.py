import uuid

import factory

from salute.people.models import (
    Permit,
    PermitActivity,
    PermitCategory,
    PermitStatus,
    PermitType,
    Person,
)


class PersonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Person

    legal_name = factory.Faker("first_name")
    preferred_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    membership_number = factory.Sequence(lambda n: n + 1)  # Incremental unique numbers
    is_suspended = factory.Faker("boolean")
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
    is_young_person = factory.Faker("boolean")

    tsa_id = factory.LazyFunction(uuid.uuid4)


class PermitActivityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PermitActivity

    name = factory.Sequence(lambda n: f"Activity {n}")


class PermitCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PermitCategory

    name = factory.Sequence(lambda n: f"Category {n}")


class PermitTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PermitType

    name = factory.Sequence(lambda n: f"Type {n}")


class PermitStatusFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PermitStatus

    name = factory.Sequence(lambda n: f"Status {n}")


class PermitFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Permit

    person = factory.SubFactory(PersonFactory)
    activity = factory.SubFactory(PermitActivityFactory)
    category = factory.SubFactory(PermitCategoryFactory)
    type = factory.SubFactory(PermitTypeFactory)
    status = factory.SubFactory(PermitStatusFactory)

    start_date = factory.Faker("date_this_year")
    date_of_permit_application = factory.Faker("date_time_this_year")
    granted_on = factory.Faker("date_time_this_year")
    expiry_date = factory.Faker("date_between", start_date="+1y", end_date="+5y")

    assessor_name = factory.Faker("name")
    restriction_details = factory.Faker("sentence")
