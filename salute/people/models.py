from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.db.models.functions import Concat
from phonenumber_field.modelfields import PhoneNumberField

from salute.integrations.tsa.models import TSAObject
from salute.roles.models import Role

if TYPE_CHECKING:
    from salute.accounts.models import User


class PersonQuerySet(models.QuerySet):
    def for_user(self, user: User) -> PersonQuerySet:
        if user.district_role_list:
            return self.all()

        return self.filter(id=user.person_id)

    def annotate_is_member(self) -> PersonQuerySet:
        return self.annotate(
            is_member=models.Exists(
                Role.objects.filter(
                    person=models.OuterRef("pk"),
                    role_type__is_member_role=True,
                ).only("id")
            )
        )

    def annotate_is_included_in_census(self) -> PersonQuerySet:
        return self.annotate(
            is_included_in_census=models.Exists(
                Role.objects.filter(
                    person=models.OuterRef("pk"),
                    role_type__included_in_census=True,
                ).only("id")
            )
        )

    def annotate_is_youth_member(self) -> PersonQuerySet:
        return self.annotate(
            is_youth_member=models.Exists(
                Role.objects.filter(
                    person=models.OuterRef("pk"),
                    role_type__is_youth_member=True,
                ).only("id")
            )
        )


PersonManager = models.Manager.from_queryset(PersonQuerySet)


class Person(TSAObject):
    # Fields synced from TSA
    legal_name = models.CharField(max_length=255, editable=False)
    preferred_name = models.CharField(max_length=255, editable=False)  # noqa: DJ001
    last_name = models.CharField(max_length=255, editable=False)
    membership_number = models.PositiveIntegerField(verbose_name="Membership Number", unique=True, editable=False)
    is_suspended = models.BooleanField(editable=False)
    default_email = models.EmailField(verbose_name="TSA Login Email", blank=True, editable=False)  # noqa: DJ001
    alternate_email = models.EmailField(verbose_name="TSA Communication Email", blank=True, editable=False)  # noqa: DJ001
    phone_number = PhoneNumberField(null=True, editable=False)
    alternate_phone_number = PhoneNumberField(null=True, editable=False)

    # Generated Fields
    first_name = models.GeneratedField(
        expression=models.Case(
            models.When(~models.Q(preferred_name__exact=""), models.F("preferred_name")),
            default=models.F("legal_name"),
        ),
        output_field=models.CharField(max_length=511),
        db_persist=True,
    )
    display_name = models.GeneratedField(
        expression=Concat(
            models.Case(
                models.When(~models.Q(preferred_name__exact=""), models.F("preferred_name")),
                default=models.F("legal_name"),
            ),
            models.Value(" "),
            models.F("last_name"),
        ),
        output_field=models.CharField(max_length=511),
        db_persist=True,
    )
    tsa_email = models.GeneratedField(
        expression=models.Case(
            models.When(~models.Q(alternate_email__exact=""), models.F("alternate_email")),
            models.When(~models.Q(default_email__exact=""), models.F("default_email")),
            default=models.Value(None),
        ),
        output_field=models.EmailField(),
        db_persist=True,
        verbose_name="TSA Preferred Email",
    )

    TSA_FIELDS = (
        "legal_name",
        "preferred_name",
        "last_name",
        "membership_number",
        "is_suspended",
        "default_email",
        "alternate_email",
        "phone_number",
        "alternate_phone_number",
    )

    objects = PersonManager()

    class Meta:
        verbose_name = "Person"
        verbose_name_plural = "People"
        ordering = ("display_name", "membership_number")

    def __str__(self) -> str:
        return f"{self.display_name} ({self.formatted_membership_number})"

    @property
    def contact_email(self) -> str:
        """
        Get the contact email for the person.

        This logic is repeated in the Person GraphQL type and this function is mostly used
        for convenience and Django Admin display.
        """
        try:
            return self.workspace_account.primary_email
        except Person.workspace_account.RelatedObjectDoesNotExist:
            return self.tsa_email

    @property
    def formatted_membership_number(self) -> str:
        return str(self.membership_number).zfill(10)
