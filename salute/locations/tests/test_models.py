import factory
import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import IntegrityError

from salute.locations.factories import (
    DistrictSiteOperatorFactory,
    GroupSiteOperatorFactory,
    SiteFactory,
    ThirdPartySiteOperatorFactory,
)


@pytest.mark.django_db
class TestSiteOperator:
    def test_district_operator(self) -> None:
        """Test creating a district operator."""
        operator = DistrictSiteOperatorFactory()
        assert operator.district is not None
        assert operator.group is None
        assert operator.name == ""

    def test_group_operator(self) -> None:
        """Test creating a group operator."""
        operator = GroupSiteOperatorFactory()
        assert operator.district is None
        assert operator.group is not None
        assert operator.name == ""

    def test_third_party_operator(self) -> None:
        """Test creating a third party operator."""
        operator = ThirdPartySiteOperatorFactory()
        assert operator.district is None
        assert operator.group is None
        assert operator.name != ""

    def test_operator_must_be_one_type(self) -> None:
        """Test that an operator cannot be multiple types."""
        with pytest.raises(ValidationError):
            operator = DistrictSiteOperatorFactory()
            operator.group = GroupSiteOperatorFactory().group
            operator.full_clean()

    def test_third_party_must_have_name(self) -> None:
        """Test that a third party operator must have a name."""
        with pytest.raises(ValidationError):
            operator = ThirdPartySiteOperatorFactory()
            operator.name = ""
            operator.full_clean()

    def test_district_cannot_have_name(self) -> None:
        """Test that a district operator cannot have a name."""
        with pytest.raises(ValidationError):
            operator = DistrictSiteOperatorFactory()
            operator.name = "Test Name"
            operator.full_clean()

    def test_unique_third_party_name(self) -> None:
        """Test that third party names must be unique."""
        name = "Test Company"
        ThirdPartySiteOperatorFactory(name=name)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ThirdPartySiteOperatorFactory(name=name)


@pytest.mark.django_db
class TestSite:
    def test_site_creation(self) -> None:
        """Test creating a site with all required fields."""
        site = SiteFactory()
        assert site.name
        assert site.tenure_type
        assert site.operator
        assert site.uprn
        assert site.street
        assert site.town
        assert site.county
        assert site.postcode
        assert site.latitude
        assert site.longitude

    def test_unique_site_name(self) -> None:
        """Test that site names must be unique."""
        name = "Test Site"
        SiteFactory(name=name)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                SiteFactory(name=name)

    def test_unique_uprn(self) -> None:
        """Test that UPRNs must be unique."""
        uprn = "000000000001"
        SiteFactory(uprn=uprn)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                SiteFactory(uprn=uprn)

    def test_uprn_format(self) -> None:
        """Test that UPRN must be exactly 12 digits."""
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                SiteFactory(uprn="123")  # Too short
        # Over-length will hit varchar length first in Postgres
        from django.db.utils import DataError

        with pytest.raises(DataError):
            with transaction.atomic():
                SiteFactory(uprn="1234567890123")  # Too long
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                SiteFactory(uprn="12345678901a")  # Contains non-digit

    def test_latitude_range(self) -> None:
        """Test that latitude must be between -90 and 90 degrees."""
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                SiteFactory(latitude=91)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                SiteFactory(latitude=-91)

    def test_longitude_range(self) -> None:
        """Test that longitude must be between -180 and 180 degrees."""
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                SiteFactory(longitude=181)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                SiteFactory(longitude=-181)

    def test_site_with_district_operator(self) -> None:
        """Test creating a site with a district operator."""
        site = SiteFactory(operator=factory.SubFactory(DistrictSiteOperatorFactory))
        assert site.operator.district is not None
        assert site.operator.group is None
        assert site.operator.name == ""

    def test_site_with_group_operator(self) -> None:
        """Test creating a site with a group operator."""
        site = SiteFactory(operator=factory.SubFactory(GroupSiteOperatorFactory))
        assert site.operator.district is None
        assert site.operator.group is not None
        assert site.operator.name == ""

    def test_site_with_third_party_operator(self) -> None:
        """Test creating a site with a third party operator."""
        site = SiteFactory(operator=factory.SubFactory(ThirdPartySiteOperatorFactory))
        assert site.operator.district is None
        assert site.operator.group is None
        assert site.operator.name != ""
