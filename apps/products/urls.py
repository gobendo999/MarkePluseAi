from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet

app_name = "products"

# DefaultRouter স্বয়ংক্রিয়ভাবে সব রুট তৈরি করে দেবে
router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")

urlpatterns = [
    path("", include(router.urls)),
]