from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from salute.core.admin import BaseModelAdminMixin
from salute.core.models import BaseModel

from .models import DistrictUserRole, ServiceAccount, User


class InlineDistrictRoleAdmin(admin.TabularInline):
    model = DistrictUserRole
    max_num = 1


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("email", "person", "service_account", "is_superuser")
    list_filter = ("is_superuser", "is_active")
    search_fields = ("email",)
    ordering = ("email",)
    readonly_fields = ("last_login", "date_joined")
    filter_horizontal = ()
    inlines = (InlineDistrictRoleAdmin,)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Person"), {"fields": ("person", "service_account", "auth0_sub")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_superuser",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "usable_password", "password1", "password2"),
            },
        ),
    )


@admin.register(ServiceAccount)
class ServiceAccountAdmin(BaseModelAdminMixin, admin.ModelAdmin):
    list_display = ("description", "user")
    search_fields = ("description", "user__email")
    list_filter = ()
    readonly_fields = ("created_at", "updated_at")
    fieldsets = ((None, {"fields": ("description", "created_at", "updated_at")}),)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return request.user.is_superuser

    def has_change_permission(self, request: HttpRequest, obj: BaseModel | None = None) -> bool:
        return request.user.is_superuser


admin.site.unregister(Group)
