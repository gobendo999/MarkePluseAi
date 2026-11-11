from rest_framework import serializers
from .models import Product, PriceHistory


# ---------------------------------------------------------
# ১. প্রাইস হিস্ট্রির সিরিয়ালাইজার
# ---------------------------------------------------------
class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = ("id", "price", "currency", "recorded_at")
        read_only_fields = fields


# ---------------------------------------------------------
# ২. মূল প্রোডাক্ট সিরিয়ালাইজার (Nested Serializer সহ)
# ---------------------------------------------------------
class ProductSerializer(serializers.ModelSerializer):
    # Nested Serializer: প্রোডাক্টের ভেতরেই দামের ওঠানামার হিস্ট্রি দেখাবে
    price_history = PriceHistorySerializer(many=True, read_only=True)
    
    # SerializerMethodField: কত টাকা দাম কমেছে তা লাইভ ক্যালকুলেশন করে দেখাবে
    price_change_summary = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "user",
            "title",
            "target_url",
            "store_name",
            "current_price",
            "currency",
            "target_price",
            "stock_status",
            "is_active",
            "price_history",
            "price_change_summary",
            "last_scraped_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "user",
            "price_history",
            "price_change_summary",
            "last_scraped_at",
            "created_at",
            "updated_at",
        )

    def get_price_change_summary(self, obj):
        """
        হিসাব করে বের করবে শুরুর দাম থেকে বর্তমান দাম কত কমেছে
        """
        history = obj.price_history.all()
        if history.count() < 2:
            return {"status": "No historical change yet", "difference": 0.00}
        
        latest_price = obj.current_price
        oldest_price = history.last().price
        diff = latest_price - oldest_price

        return {
            "initial_price": float(oldest_price),
            "current_price": float(latest_price),
            "currency": obj.currency,
            "difference": float(diff),
            "dropped": diff < 0,
        }

    def validate_target_url(self, value):
        """
        URL ভ্যালিডেশন: লিংকটি http বা https দিয়ে শুরু হতে হবে
        """
        if not value.startswith("http://") and not value.startswith("https://"):
            raise serializers.ValidationError("URL must start with http:// or https://")
        return value

    def create(self, validated_data):
        """
        স্বয়ংক্রিয়ভাবে বর্তমান লগইন থাকা ইউজারকে অ্যাসাইন করা
        """
        user = self.context["request"].user
        return Product.objects.create(user=user, **validated_data)
