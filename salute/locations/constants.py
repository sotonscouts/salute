from django.db import models


class TenureType(models.TextChoices):
    FREEHOLD = "Freehold"
    LEASEHOLD = "Leasehold"
    RENTED = "Rented"
