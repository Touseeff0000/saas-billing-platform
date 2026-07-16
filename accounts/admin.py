from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ["username", "email", "tenant", "role", "is_staff"]
    fieldsets = UserAdmin.fieldsets + (
        ("Tenant info", {"fields": ("tenant", "role")}),
    )