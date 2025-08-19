from django.db import models

from salute.core.models import BaseModel
from salute.hierarchy.models import Section


class OSMSyncLog(BaseModel):
    date = models.DateField()
    data = models.JSONField()
    error = models.TextField(blank=True)
    success = models.BooleanField()

    def __str__(self) -> str:
        return f"{self.date} - {self.success}"

    class Meta:
        ordering = ("-date",)


class OSMSectionHeadcountRecord(BaseModel):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="osm_section_headcount_records")
    date = models.DateField()

    sync_log = models.ForeignKey(
        OSMSyncLog, on_delete=models.SET_NULL, null=True, related_name="osm_section_headcount_records"
    )
    young_person_count = models.IntegerField()
    adult_count = models.IntegerField()

    class Meta:
        ordering = ("date",)
        constraints = [models.UniqueConstraint(fields=["section", "date"], name="unique_section_date")]

    def __str__(self) -> str:
        return f"{self.section.display_name} - {self.date} - {self.young_person_count}"
