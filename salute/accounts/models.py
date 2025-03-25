from __future__ import annotations

from functools import cached_property
from typing import Any, TypeVar

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
)
from django.contrib.auth.models import (
    UserManager as DjangoUserManager,
)
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_choices_field import TextChoicesField

from salute.core.models import BaseModel

_T = TypeVar("_T", bound=models.Model)


class UserManager[_T](DjangoUserManager):
    def _create_user(self, email: str, password: str | None, **extra_fields: Any) -> _T:
        """
        Create and save a user with the given email, and password.
        """
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields: Any) -> _T:  # type: ignore[override]
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None = None, **extra_fields: Any) -> _T:  # type: ignore[override]
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_("email address"), unique=True)
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    auth0_sub = models.CharField(
        verbose_name="Auth0 Subject",
        help_text="Do not edit if you do not understand. Maps to sub in OIDC token",
        max_length=255,
        blank=True,
        null=True,
        unique=True,
    )
    person = models.OneToOneField("people.Person", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    @property
    def is_staff(self) -> bool:
        return self.is_superuser

    def clean(self) -> None:
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self) -> str:
        """
        Return the first_name plus the last_name, with a space in between.
        """
        if self.person:
            return self.person.display_name
        return self.email

    def get_short_name(self) -> str:
        """Return the short name for the user."""
        if self.person:
            return self.person.first_name
        return self.email

    def email_user(self, subject: str, message: str, from_email: str | None = None, **kwargs: Any) -> None:
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    @cached_property
    def district_role_list(self) -> list[DistrictUserRoleType]:
        return [dr.level for dr in self.district_roles.only("level")]


class DistrictUserRoleType(models.TextChoices):
    ADMIN = "Admin"
    MANAGER = "Manager"


class DistrictUserRole(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="district_roles")
    district = models.ForeignKey("hierarchy.District", on_delete=models.PROTECT, related_name="+")
    level = TextChoicesField(choices_enum=DistrictUserRoleType)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "district"],
                violation_error_message="A user can only have one district role",
                name="one_district_role_per_user",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user} is {self.level} for {self.district}"
