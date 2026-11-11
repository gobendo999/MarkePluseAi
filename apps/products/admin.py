from django.contrib import admin
from .models import Product, PriceHistory


# ---------------------------------------------------------
# ১. প্রোডাক্টের ভেতরেই প্রাইস হিস্ট্রি টেবিল দেখার জন্য Inline
# ---------------------------------------------------------
class PriceHistoryInline(admin.TabularInline):
    model = PriceHistory
    extra = 0
    readonly_fields = ("price", "recorded_at")
    can_delete = False
    ordering = ("-recorded_at",)


# ---------------------------------------------------------
# ২. মূল Product Admin কনফিগারেশন
# ---------------------------------------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "store_name",
        "current_price",
        "stock_status",
        "is_active",
        "is_deleted",
        "created_at",
    )
    list_filter = ("store_name", "stock_status", "is_active", "is_deleted", "created_at")
    search_fields = ("title", "target_url", "user__email", "store_name")
    readonly_fields = ("id", "created_at", "updated_at", "last_scraped_at")
    inlines = [PriceHistoryInline]

    # অ্যাডমিন থেকে এক ক্লিকে অনেকগুলো প্রোডাক্টের স্টক পরিবর্তন করার অ্যাকশন
    actions = ["mark_in_stock", "mark_out_of_stock"]

    @admin.action(description="Mark selected products as In Stock")
    def mark_in_stock(self, request, queryset):
        queryset.update(stock_status=Product.StockStatus.IN_STOCK)

    @admin.action(description="Mark selected products as Out of Stock")
    def mark_out_of_stock(self, request, queryset):
        queryset.update(stock_status=Product.StockStatus.OUT_OF_STOCK)


# ---------------------------------------------------------
# ৩. আলাদাভাবে Price History দেখার জন্য
# ---------------------------------------------------------
@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ("product", "price", "recorded_at")
    list_filter = ("recorded_at",)
    search_fields = ("product__title",)