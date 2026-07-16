from django.db import models
from tenants.models import Tenant


class Plan(models.Model):
    name = models.CharField(max_length=100)
    stripe_price_id = models.CharField(max_length=100, blank=True)
    monthly_price = models.DecimalField(max_digits=8, decimal_places=2)
    max_records = models.PositiveIntegerField(help_text="Usage limit for this plan")

    def __str__(self):
        return self.name


class Subscription(models.Model):
    STATUS_CHOICES = (
        ("active", "Active"),
        ("past_due", "Past Due"),
        ("canceled", "Canceled"),
        ("trialing", "Trialing"),
    )
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name="subscription")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="trialing")
    current_period_end = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.tenant.name} - {self.plan.name} ({self.status})"


class UsageRecord(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="usage_records")
    count = models.PositiveIntegerField(default=0)
    period_start = models.DateField()

    class Meta:
        unique_together = ("tenant", "period_start")

    def __str__(self):
        return f"{self.tenant.name} - {self.period_start}: {self.count}"