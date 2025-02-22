from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

from .models import DistrictUserRole, User


class InlineDistrictRoleAdmin(admin.TabularInline):
    model = DistrictUserRole
    max_num = 1


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("email", "is_superuser")
    list_filter = ("is_superuser", "is_active")
    search_fields = ("email",)
    ordering = ("email",)
    readonly_fields = ("last_login", "date_joined")
    filter_horizontal = ()
    inlines = (InlineDistrictRoleAdmin,)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Person"), {"fields": ("person",)}),
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


admin.site.unregister(Group)
