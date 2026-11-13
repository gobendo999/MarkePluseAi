"""
Topic 30: ASGI Config with Django Channels Protocol Routing.
Exposes ProtocolTypeRouter handling both HTTP and WebSocket traffic.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'price_tracking.settings')

# ১. জ্যাঙ্গো এএসজিআই অ্যাপ্লিকেশন ইনিশিয়ালাইজ করা
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import apps.products.routing

# ২. প্রোটোকল টাইপ রাউটার: HTTP ট্রাফিক যাবে জ্যাঙ্গোতে, WebSocket ট্রাফিক যাবে চ্যানেলে
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            apps.products.routing.websocket_urlpatterns
        )
    ),
})
