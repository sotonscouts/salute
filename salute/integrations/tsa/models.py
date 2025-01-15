from django.db import models

from salute.core.models import BaseModel


class TSAObject(BaseModel):
    tsa_id = models.UUIDField(verbose_name="TSA ID", unique=True, editable=False)
    TSA_FIELDS: tuple[str, ...] = ()

    class Meta:
        abstract = True


class TSATimestampedObject(TSAObject):
    tsa_last_modified = models.DateTimeField(verbose_name="TSA Last Modified at", editable=False)

    TSA_FIELDS: tuple[str, ...] = ()

    class Meta:
        abstract = True


class TSATaxonomy(TSAObject):
    name = models.CharField(max_length=255)

    TSA_FIELDS = ("name",)

    class Meta:
        abstract = True
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name
