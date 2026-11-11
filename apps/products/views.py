from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.db.models import Min, Max, Avg
from django.utils import timezone
from .pagination import StandardResultsSetPagination
from .models import Product, PriceHistory
from .serializers import ProductSerializer, PriceHistorySerializer
from .permissions import IsOwnerOnly
from apps.scraper.services import ScraperService
from apps.scraper.tasks import scrape_product_task
from .ai_service import MarketIntelligenceAIService


@extend_schema_view(
    list=extend_schema(summary="List all tracked products for logged-in user"),
    create=extend_schema(summary="Add a new competitor product to track"),
    retrieve=extend_schema(summary="Get details of a specific tracked product"),
    partial_update=extend_schema(summary="Update product details (e.g. target price)"),
    destroy=extend_schema(summary="Soft-delete a product tracker"),
)
class ProductViewSet(viewsets.ModelViewSet):
    """
    Topic 38: Full CRUD ModelViewSet with custom action endpoints.
    Topic 22: Query optimization using select_related and prefetch_related.
    """
    serializer_class = ProductSerializer
    permission_classes = [IsOwnerOnly]
    pagination_class = StandardResultsSetPagination   
    def get_queryset(self):
        """
        সাধারণ ইউজার শুধু তার নিজের প্রোডাক্ট দেখতে পাবে,
        এডমিন চাইলে সিস্টেমের সব প্রোডাক্ট দেখতে পারবে।
        Topic 22: N+1 সমস্যা দূর করার জন্য select_related ও prefetch_related ব্যবহার করা হয়েছে।
        """
        user = self.request.user
        if user.is_staff:
            qs = Product.objects.all()
        else:
            qs = Product.objects.filter(user=user)

        return qs.select_related("user").prefetch_related("price_history")

    # ---------------------------------------------------------
    # Custom Action (Topic 38): দামের সর্বোচ্চ, সর্বনিম্ন ও গড় পরিসংখ্যান
    # Endpoint: GET /api/products/{id}/price-stats/
    # ---------------------------------------------------------
    @extend_schema(
        summary="Get price fluctuation statistics for a product",
        description="Calculates minimum, maximum, and average historical prices.",
    )
    @action(detail=True, methods=["get"], url_path="price-stats")
    def price_stats(self, request, pk=None):
        product = self.get_object()
        history = product.price_history.all()

        if not history.exists():
            return Response(
                {"message": "No historical price records available yet."},
                status=status.HTTP_404_NOT_FOUND,
            )

        stats = history.aggregate(
            lowest_price=Min("price"),
            highest_price=Max("price"),
            average_price=Avg("price"),
        )

        return Response({
            "product_id": product.id,
            "title": product.title,
            "current_price": float(product.current_price),
            "currency": product.currency,
            "lowest_price": float(stats["lowest_price"] or 0),
            "highest_price": float(stats["highest_price"] or 0),
            "average_price": round(float(stats["average_price"] or 0), 2),
            "total_records": history.count(),
        })

    # ---------------------------------------------------------
    # Custom Action (Topic 38): টেস্ট করার জন্য কৃত্রিম প্রাইস ড্রপ তৈরি করা
    # Endpoint: POST /api/products/{id}/simulate-price-drop/
    # ---------------------------------------------------------
    @extend_schema(summary="Simulate a price change for testing price alerts")
    @action(detail=True, methods=["post"], url_path="simulate-price-drop")
    def simulate_price_drop(self, request, pk=None):
        product = self.get_object()
        new_price = request.data.get("new_price")

        if not new_price:
            return Response(
                {"error": "Please provide 'new_price' in request body."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # নতুন দাম হিস্ট্রিতে যোগ করা এবং বর্তমান দাম আপডেট করা
        PriceHistory.objects.create(
            product=product,
            price=new_price,
            currency=product.currency,
        )
        product.current_price = new_price
        product.save(update_fields=["current_price", "updated_at"])

        return Response(
            {"message": f"Price updated to {new_price} {product.currency} successfully!", "product": ProductSerializer(product).data},
            status=status.HTTP_200_OK,
        )

    # ---------------------------------------------------------
    # Custom Action (Topic 38 & 25): লাইভ ওয়েবসাইট স্ক্র্যাপ করা (Asynchronous Celery Task)
    # Endpoint: POST /api/products/{id}/scrape-now/
    # ---------------------------------------------------------
    @extend_schema(summary="Trigger real-time live scraper for this product URL asynchronously")
    @action(detail=True, methods=["post"], url_path="scrape-now")
    def scrape_now(self, request, pk=None):
        product = self.get_object()

        # .delay() দিয়ে ব্যাকগ্রাউন্ডে সেলেরি টাস্ক চালু করা
        task = scrape_product_task.delay(str(product.id))

        return Response({
            "message": "Scraping task queued in background successfully!",
            "task_id": task.id,
            "product_id": product.id,
            "status": "PENDING"
        }, status=status.HTTP_202_ACCEPTED)

    # ---------------------------------------------------------
    # Custom Action (Topic 46): Google Gemini AI Market Intelligence
    # Endpoint: POST /api/products/{id}/ai-insights/
    # ---------------------------------------------------------
    @extend_schema(summary="Generate AI-powered market intelligence & price verdict using Google Gemini")
    @action(detail=True, methods=["post", "get"], url_path="ai-insights")
    def ai_insights(self, request, pk=None):
        product = self.get_object()
        user = request.user

        # ১. ক্রেডিট ব্যালেন্স যাচাই করা (টপিক ২১ এর সাথে ইন্টিগ্রেশন)
        if user.credits_balance <= 0 and not user.is_staff:
            return Response({
                "error": "Insufficient AI credits. Upgrade to PRO or purchase more credits to run AI Market Intelligence."
            }, status=status.HTTP_402_PAYMENT_REQUIRED)

        # ২. Gemini AI সার্ভিস কল করা
        ai_result = MarketIntelligenceAIService.generate_product_insights(product)

        if not ai_result.get("success"):
            return Response({
                "error": ai_result.get("error")
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # ৩. সফল হলে ইউজারের অ্যাকাউন্ট থেকে ১ ক্রেডিট কেটে নেওয়া
        if not user.is_staff:
            user.credits_balance -= 1
            user.save(update_fields=["credits_balance"])

        return Response({
            "product_id": str(product.id),
            "product_title": product.title,
            "current_price": f"{product.current_price} {product.currency}",
            "remaining_credits": user.credits_balance,
            "ai_insights": ai_result["data"]
        }, status=status.HTTP_200_OK)
