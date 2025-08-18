from django.contrib import admin

from salute.core.admin import BaseModelAdminMixin
from salute.integrations.osm.models import OSMSectionHeadcountRecord, OSMSyncLog


@admin.register(OSMSyncLog)
class OSMSyncLogAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    list_display = ("date", "success", "created_at")
    list_filter = ("success", "date")
    search_fields = ("error",)


@admin.register(OSMSectionHeadcountRecord)
class OSMSectionHeadcountRecordAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    list_display = ("section", "date", "young_person_count", "sync_log")
    list_filter = ("date", "section__group", "section__section_type")
    raw_id_fields = ("section", "sync_log")
