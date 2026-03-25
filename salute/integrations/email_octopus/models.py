from django.db import models
from django_choices_field import TextChoicesField

from salute.core.models import BaseModel


class EmailOctopusStatus(models.TextChoices):
    PENDING = "pending"
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"


class EmailOctopusContact(BaseModel):
    contact_id = models.UUIDField(verbose_name="Email Octopus Contact ID", unique=True)
    person = models.OneToOneField(
        "people.Person", null=True, on_delete=models.SET_NULL, related_name="email_octopus_contact"
    )
    status = TextChoicesField(choices_enum=EmailOctopusStatus, editable=False, default=EmailOctopusStatus.SUBSCRIBED)
