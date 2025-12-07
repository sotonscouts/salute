from django.db import models

from salute.core.models import BaseModel


class WifiAccountGroup(BaseModel):
    slug = models.SlugField(max_length=128, unique=True)
    name = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "WiFi Account Group"
        verbose_name_plural = "WiFi Account Groups"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["is_default"],
                condition=models.Q(is_default=True),
                name="unique_default_wifi_account_group",
                violation_error_message="Only one default WiFi account group is allowed.",
            ),
        ]


class WifiAccount(BaseModel):
    person = models.OneToOneField("people.Person", on_delete=models.CASCADE, related_name="wifi_account")
    group = models.ForeignKey(WifiAccountGroup, on_delete=models.PROTECT, related_name="wifi_accounts")
    username = models.CharField(max_length=128, unique=True)
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.person.display_name} ({self.username})"

    class Meta:
        verbose_name = "WiFi Account"
        verbose_name_plural = "WiFi Accounts"
        ordering = ["username"]
