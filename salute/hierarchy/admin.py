# from django.contrib import admin
# from django.http import HttpRequest

# from salute.hierarchy.models import District, Group, Section
# from salute.integrations.tsa.admin import TSAObjectModelAdminMixin


# @admin.register(District)
# class DistrictAdmin(TSAObjectModelAdminMixin, admin.ModelAdmin):
#     list_display = ("unit_name",)
#     search_fields = ("unit_name", "tsa_id")

#     fieldsets = (
#         (None, {"fields": ("unit_name",)}),
#     ) + TSAObjectModelAdminMixin.FIELDSETS

#     def has_change_permission(self, request: HttpRequest, obj: District | None = None) -> bool:
#         return False  # Currently nothing to change


# @admin.register(Group)
# class GroupAdmin(TSAObjectModelAdminMixin, admin.ModelAdmin):
#     list_display = (
#         "unit_name",
#         "local_unit_number",
#         "location_name",
#         "district",
#         "group_type",
#     )
#     list_filter = ("group_type",)
#     search_fields = ("unit_name", "tsa_id", "location_name")

#     fieldsets = (
#         (None, {"fields": ("unit_name", "district")}),
#         (
#             "Group",
#             {
#                 "fields": (
#                     "location_name",
#                     "local_unit_number_ordinal",
#                     "group_type",
#                     "charity_number",
#                 )
#             },
#         ),
#     ) + TSAObjectModelAdminMixin.FIELDSETS


# @admin.register(Section)
# class SectionAdmin(TSAObjectModelAdminMixin, admin.ModelAdmin):
#     list_display = ("unit_name", "section_type", "group", "district")
#     list_filter = ("section_type", "group")
#     search_fields = ("unit_name", "tsa_id")

#     fieldsets = (
#         (None, {"fields": ("unit_name", "district", "group")}),
#         ("Section", {"fields": ("section_type",)}),
#     ) + TSAObjectModelAdminMixin.FIELDSETS
