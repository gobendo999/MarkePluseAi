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

        # ---------------------------------------------------------
        # Topic 30: Broadcast Live Price Drop via WebSockets
        # ---------------------------------------------------------
        if new_price > 0 and old_price > 0 and new_price < old_price:
            try:
                from asgiref.sync import async_to_sync
                from channels.layers import get_channel_layer

                channel_layer = get_channel_layer()
                if channel_layer:
                    drop_percent = round(float((old_price - new_price) / old_price * 100), 1)
                    alert_payload = {
                        "product_id": str(product.id),
                        "title": product.title,
                        "old_price": float(old_price),
                        "new_price": float(new_price),
                        "currency": product.currency,
                        "drop_percent": drop_percent,
                        "store_name": product.store_name,
                        "target_url": product.target_url,
                        "message": f"🔥 Price dropped by {drop_percent}%! {product.title} is now {new_price} {product.currency}",
                    }
                    async_to_sync(channel_layer.group_send)(
                        "price_alerts",
                        {
                            "type": "price_drop_alert",
                            "data": alert_payload,
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to broadcast WebSocket price drop: {e}")

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
@shared_task
def periodic_scrape_all_active_products():
    """
    Topic 48: Celery Beat Periodic Scheduler
    ডাটাবেজের সব অ্যাক্টিভ প্রোডাক্ট খুঁজে প্রতিটি প্রোডাক্টের জন্য ব্যাকগ্রাউন্ড স্ক্র্যাপিং টাস্ক চালু করে।
    """
    active_products = Product.objects.filter(is_deleted=False)
    dispatched_count = 0
    for product in active_products:
        scrape_product_task.delay(product.id)
        dispatched_count += 1
    
    logger.info(f"[Celery Beat] Dispatched {dispatched_count} periodic scrape tasks.")
    return f"Successfully dispatched {dispatched_count} scraping tasks."
