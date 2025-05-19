from django.core.exceptions import ValidationError
from django.db import models
from django_choices_field import TextChoicesField

from salute.core.models import BaseModel
from salute.hierarchy.models import District, Group
from salute.locations.constants import TenureType


class SiteOperator(BaseModel):
    """A site operator can be a district, group or third party."""

    name = models.CharField(max_length=255, blank=True, db_index=True)
    district = models.OneToOneField(
        District, on_delete=models.PROTECT, null=True, blank=True, related_name="site_operator"
    )
    group = models.OneToOneField(Group, on_delete=models.PROTECT, null=True, blank=True, related_name="site_operator")

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    (models.Q(district__isnull=False) & models.Q(group__isnull=True) & models.Q(name=""))
                    | (models.Q(district__isnull=True) & models.Q(group__isnull=False) & models.Q(name=""))
                    | (models.Q(district__isnull=True) & models.Q(group__isnull=True) & ~models.Q(name=""))
                ),
                name="site_operator_must_be_one_type",
                violation_error_message="A site operator must be either a district, group, or third party, but not multiple types. District and group operators must have blank names, while third party operators must have a name.",  # noqa: E501
            ),
            models.UniqueConstraint(
                fields=["name"],
                condition=~models.Q(name__exact=""),
                name="unique_third_party_name",
                violation_error_message="Third party operators must have a unique name.",
            ),
        ]

    @property
    def display_name(self) -> str:
        if self.district:
            return self.district.display_name
        if self.group:
            return self.group.display_name
        return self.name

    def clean(self) -> None:
        super().clean()
        if self.district is None and self.group is None and not self.name:
            raise ValidationError("Third party operators must have a name")
        elif (self.district is not None or self.group is not None) and self.name:
            raise ValidationError("Only third party operators can have a name")

    def __str__(self) -> str:
        return self.display_name


class Site(BaseModel):
    """A physical location that can be used for Scouting."""

    name = models.CharField(max_length=255, unique=True)
    tenure_type = TextChoicesField(choices_enum=TenureType)
    operator = models.ForeignKey(SiteOperator, on_delete=models.PROTECT, related_name="sites")

    # Address fields
    uprn = models.CharField(
        verbose_name="UPRN",
        max_length=12,
        unique=True,
        help_text="Unique Property Reference Number (12 digits)",
    )
    building_name = models.CharField(max_length=255, blank=True)
    street_number = models.CharField(max_length=10, blank=True)
    street = models.CharField(max_length=255)
    town = models.CharField(max_length=255)
    county = models.CharField(max_length=255)
    postcode = models.CharField(max_length=10)

    # Location coordinates
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(latitude__gte=-90) & models.Q(latitude__lte=90),
                name="latitude_range",
                violation_error_message="Latitude must be between -90 and 90 degrees.",
            ),
            models.CheckConstraint(
                condition=models.Q(longitude__gte=-180) & models.Q(longitude__lte=180),
                name="longitude_range",
                violation_error_message="Longitude must be between -180 and 180 degrees.",
            ),
            models.CheckConstraint(
                condition=models.Q(uprn__regex=r"^\d{12}$"),
                name="uprn_format",
                violation_error_message="UPRN must be exactly 12 digits.",
            ),
        ]

    def __str__(self) -> str:
        return self.name
