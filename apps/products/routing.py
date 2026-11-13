from django.urls import re_path
from . import consumers

# -------------------------------------------------------------
# Topic 30: WebSocket URL Routing
# -------------------------------------------------------------
websocket_urlpatterns = [
    re_path(r"^ws/price-alerts/$", consumers.PriceAlertConsumer.as_asgi()),
]
