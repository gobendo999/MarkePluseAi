from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = (
        "email",
        "full_name",
        "role",
        "credits_balance",
        "is_staff",
        "is_active",
        "date_joined",
    )
    list_filter = ("role", "is_staff", "is_active", "date_joined")
    search_fields = ("email", "full_name")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("full_name",)}),
        ("Permissions & Roles", {"fields": ("role", "credits_balance", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined", "updated_at")}),
    )
    readonly_fields = ("date_joined", "updated_at", "last_login")

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "full_name", "role", "credits_balance", "password1", "password2"),
            },
        ),
    )
