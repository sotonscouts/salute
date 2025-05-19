import factory
from factory.django import DjangoModelFactory
from factory.faker import Faker

from salute.hierarchy.factories import DistrictFactory, GroupFactory
from salute.locations.models import Site, SiteOperator, TenureType


class BaseSiteOperatorFactory(DjangoModelFactory):
    """Base factory for SiteOperator instances."""

    class Meta:
        model = SiteOperator


class DistrictSiteOperatorFactory(BaseSiteOperatorFactory):
    """Factory for creating district operators."""

    district = factory.SubFactory(DistrictFactory)
    group = None
    name = ""


class GroupSiteOperatorFactory(BaseSiteOperatorFactory):
    """Factory for creating group operators."""

    district = None
    group = factory.SubFactory(GroupFactory)
    name = ""


class ThirdPartySiteOperatorFactory(BaseSiteOperatorFactory):
    """Factory for creating third party operators."""

    district = None
    group = None
    name = Faker("company", locale="en_GB")


class SiteFactory(DjangoModelFactory):
    """Factory for creating Site instances."""

    class Meta:
        model = Site

    name = Faker("company", locale="en_GB")
    tenure_type = factory.Iterator(TenureType.values)
    operator = factory.SubFactory(ThirdPartySiteOperatorFactory)  # Default to third party

    # Address fields
    uprn = factory.Sequence(lambda n: f"{n:012d}")  # Generates 12-digit numbers with leading zeros
    building_name = Faker("secondary_address", locale="en_GB")
    street_number = Faker("building_number", locale="en_GB")
    street = Faker("street_name", locale="en_GB")
    town = Faker("city", locale="en_GB")
    county = Faker("county", locale="en_GB")
    postcode = Faker("postcode", locale="en_GB")

    # Location coordinates
    latitude = factory.Faker("latitude", locale="en_GB")
    longitude = factory.Faker("longitude", locale="en_GB")
