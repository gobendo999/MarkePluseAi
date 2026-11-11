import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email).lower()
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", CustomUser.Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Enterprise Custom User Model with RBAC and credit tracking.
    """
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrator"
        ENTERPRISE = "ENTERPRISE", "Enterprise User"
        PRO = "PRO", "Pro Subscriber"
        FREE = "FREE", "Free Tier"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=255, blank=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.FREE,
        db_index=True,
    )
    credits_balance = models.PositiveIntegerField(
        default=25,
        help_text="Available credits for scraping and AI report generation",
    )
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    @property
    def is_pro_or_enterprise(self):
        return self.role in [self.Role.PRO, self.Role.ENTERPRISE, self.Role.ADMIN]

    def deduct_credits(self, amount: int = 1) -> bool:
        """
        Deducts credit balance if user has sufficient credits.
        """
        if self.credits_balance >= amount:
            self.credits_balance -= amount
            self.save(update_fields=["credits_balance", "updated_at"])
            return True
        return False
