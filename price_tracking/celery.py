import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'price_tracking.settings')
app = Celery('price_tracking')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


app.conf.beat_schedule = {
    # প্রতিদিন মধ্যরাত ১২:০০ টায় স্বয়ংক্রিয়ভাবে চলবে
    "daily-price-scrape-midnight": {
        "task": "apps.scraper.tasks.periodic_scrape_all_active_products",
        "schedule": crontab(hour=0, minute=0),
    },
    # প্রতি ৬ ঘণ্টা পর পর চেক করবে
    "scrape-active-products-every-6-hours": {
        "task": "apps.scraper.tasks.periodic_scrape_all_active_products",
        "schedule": crontab(minute=0, hour="*/6"),
    },
}