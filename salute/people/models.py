from django.db import models
from django.db.models.functions import Coalesce, Concat
from phonenumber_field.modelfields import PhoneNumberField

from salute.integrations.tsa.models import TSAObject


class Person(TSAObject):
    # Fields synced from TSA
    legal_name = models.CharField(max_length=255, editable=False)
    preferred_name = models.CharField(null=True, max_length=255, editable=False)  # noqa: DJ001
    last_name = models.CharField(max_length=255, editable=False)
    membership_number = models.PositiveIntegerField(verbose_name="Membership Number", unique=True, editable=False)
    is_suspended = models.BooleanField(editable=False)
    primary_email = models.EmailField(null=True, editable=False)  # noqa: DJ001
    default_email = models.EmailField(null=True, editable=False)  # noqa: DJ001
    alternate_email = models.EmailField(null=True, editable=False)  # noqa: DJ001
    phone_number = PhoneNumberField(null=True, editable=False)
    alternate_phone_number = PhoneNumberField(null=True, editable=False)

    # Generated Fields
    first_name = models.GeneratedField(
        expression=models.functions.Coalesce(models.F("preferred_name"), models.F("legal_name")),
        output_field=models.CharField(max_length=511),
        db_persist=True,
    )
    display_name = models.GeneratedField(
        expression=Concat(models.F("first_name"), models.Value(" "), models.F("last_name")),
        output_field=models.CharField(max_length=511),
        db_persist=True,
    )
    tsa_email = models.GeneratedField(
        expression=Coalesce(
            models.F("primary_email"),
            models.F("default_email"),
            models.F("alternate_email"),
        ),
        output_field=models.EmailField(),
        db_persist=True,
    )

    TSA_FIELDS = (
        "legal_name",
        "preferred_name",
        "last_name",
        "membership_number",
        "is_suspended",
        "primary_email",
        "default_email",
        "alternate_email",
        "phone_number",
        "alternate_phone_number",
    )

    class Meta:
        verbose_name = "Person"
        verbose_name_plural = "People"

    def __str__(self) -> str:
        return f"{self.display_name} ({self.formatted_membership_number})"

    @property
    def contact_email(self) -> str:
        try:
            return self.workspace_account.primary_email
        except Person.workspace_account.RelatedObjectDoesNotExist:
            return self.tsa_email

    @property
    def formatted_membership_number(self) -> str:
        return str(self.membership_number).zfill(10)
