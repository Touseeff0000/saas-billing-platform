from django.contrib.auth.models import AbstractUser
from django.db import models
from tenants.models import Tenant


class User(AbstractUser):
    ROLE_CHOICES = (
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("member", "Member"),
    )
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="users",
        null=True, blank=True
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")

    def __str__(self):
        return f"{self.username} ({self.tenant})"