from django.contrib import admin
from django.http.request import HttpRequest

from salute.wifi.models import WifiAccount, WifiAccountGroup


@admin.register(WifiAccountGroup)
class WifiAccountGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_default")
    list_filter = ("is_default",)
    search_fields = ("name", "slug")


@admin.register(WifiAccount)
class WifiAccountAdmin(admin.ModelAdmin):
    list_display = ("person", "username", "group", "is_active")
    list_filter = ("is_active", "group")
    search_fields = ("person__display_name", "username")
    fields = ("person", "group", "username", "password", "is_active")

    def get_create_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: WifiAccount | None = None) -> bool:
        return request.user.is_superuser

    def has_delete_permission(self, request: HttpRequest, obj: WifiAccount | None = None) -> bool:
        return False

    def get_readonly_fields(self, request: HttpRequest, obj: WifiAccount | None = None) -> list[str]:
        return super().get_readonly_fields(request, obj) + ("person", "password")  # type: ignore
