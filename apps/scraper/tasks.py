import logging
from celery import shared_task
from django.utils import timezone
from apps.products.models import Product, PriceHistory
from .services import ScraperService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def scrape_product_task(self, product_id):
    """
    Topic 25: Asynchronous Background Scraper Task
    Runs in Celery worker thread without blocking the HTTP request thread.
    """
    try:
        product = Product.objects.get(id=product_id, is_deleted=False)
        logger.info(f"Starting async scrape for Product: {product.id}")

        # হেডলেস স্ক্র্যাপার দিয়ে ডাটা আনা
        scraped_data = ScraperService.scrape_product(product.target_url)

        if not scraped_data.get("success"):
            return {"success": False, "error": scraped_data.get("error")}

        # ডাটাবেজ আপডেট করা
        old_price = product.current_price
        new_price = scraped_data["price"]

        product.title = scraped_data["title"]
        product.current_price = new_price
        product.currency = scraped_data.get("currency", product.currency)
        product.store_name = scraped_data["store_name"]
        product.stock_status = scraped_data["stock_status"]
        product.last_scraped_at = timezone.now()
        product.save()

        # দাম কমলে বা বাড়লে হিস্ট্রিতে রেকর্ড যোগ করা
        if new_price > 0 and (old_price != new_price or not product.price_history.exists()):
            PriceHistory.objects.create(
                product=product,
                price=new_price,
                currency=product.currency,
            )

        return {
            "success": True,
            "product_id": str(product.id),
            "new_price": float(new_price),
        }

    except Product.DoesNotExist:
        return {"success": False, "error": "Product not found"}
    except Exception as exc:
        # নেটওয়ার্ক সমস্যা হলে ৬০ সেকেন্ড বিরতি দিয়ে রিট্রাই করবে
        raise self.retry(exc=exc, countdown=60)
