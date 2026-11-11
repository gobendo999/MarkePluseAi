import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


# ---------------------------------------------------------
# 1. Models Level 2: Soft Delete QuerySet & Manager
# ---------------------------------------------------------
class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        # আসল ডাটা না মুছে শুধু ফ্ল্যাগ অন করা
        return self.update(is_deleted=True, updated_at=timezone.now())

    def hard_delete(self):
        # ডাটাবেজ থেকে চিরতরে মুছে ফেলা
        return super().delete()

    def alive(self):
        return self.filter(is_deleted=False)


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        # বাই-ডিফল্ট শুধু একটিভ (যা ডিলিট হয়নি) ডাটা আনবে
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)


# ---------------------------------------------------------
# 2. Main Product Tracker Model
# ---------------------------------------------------------
class Product(models.Model):
    class StockStatus(models.TextChoices):
        IN_STOCK = "IN_STOCK", "In Stock"
        OUT_OF_STOCK = "OUT_OF_STOCK", "Out of Stock"
        UNKNOWN = "UNKNOWN", "Unknown"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products",
    )
    title = models.CharField(max_length=500, blank=True, default="Pending Scrape...")
    target_url = models.URLField(max_length=1000)
    store_name = models.CharField(max_length=100, blank=True, default="Generic")
    
    current_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    #currency check 
    currency = models.CharField(max_length=10, default="USD", help_text="e.g. USD, BDT, EUR, INR")
    target_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock_status = models.CharField(
        max_length=20,
        choices=StockStatus.choices,
        default=StockStatus.UNKNOWN,
    )

    is_active = models.BooleanField(default=True, help_text="Track actively via Celery")
    is_deleted = models.BooleanField(default=False)
    
    last_scraped_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Managers (Level 2)
    objects = SoftDeleteManager()      # Product.objects.all() -> শুধু ডিলিট না হওয়াগুলো আনবে
    all_objects = models.Manager()      # Product.all_objects.all() -> ডিলিট হওয়াগুলোসহ সব আনবে

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["store_name"]),
        ]
        # Level 2 Constraints
        constraints = [
            # একই ইউজার একই URL যেন একাধিকবার যোগ করতে না পারে (ডিলিট ছাড়া)
            models.UniqueConstraint(
                fields=["user", "target_url"],
                condition=models.Q(is_deleted=False),
                name="unique_active_product_per_user",
            ),
            # দাম কখনো মাইনাস হওয়া যাবে না
            models.CheckConstraint(
                check=models.Q(current_price__gte=0),
                name="product_current_price_non_negative",
            ),
        ]

    def __str__(self):
        return f"{self.title[:40]} - {self.store_name} ({self.current_price})"

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.save(update_fields=["is_deleted", "updated_at"])


# ---------------------------------------------------------
# 3. Price History Model (দামের ওঠানামার ইতিহাস)
# ---------------------------------------------------------
class PriceHistory(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="price_history",
    )
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")
    recorded_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-recorded_at"]
        verbose_name_plural = "Price histories"
        indexes = [
            models.Index(fields=["product", "-recorded_at"]),
        ]

    def __str__(self):
        return f"{self.product.title[:20]} -> {self.price} @ {self.recorded_at.strftime('%Y-%m-%d %H:%M')}"