import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class PriceAlertConsumer(AsyncWebsocketConsumer):
    """
    Topic 30: Real-Time Live Price Drop WebSocket Consumer
    Handles persistent two-way WebSocket connections for live price drop notifications.
    """

    async def connect(self):
        user = self.scope.get("user")
        if user and user.is_authenticated:
            self.user_group = f"user_{user.id}"
        else:
            self.user_group = "anonymous_alerts"

        self.broadcast_group = "price_alerts"

        # ১. ইউজারকে ব্রডকাস্ট গ্রুপে যুক্ত করা
        await self.channel_layer.group_add(
            self.broadcast_group,
            self.channel_name
        )

        # ২. ইউজার লগইন থাকলে তার পার্সোনাল গ্রুপেও যুক্ত করা
        if self.user_group != "anonymous_alerts":
            await self.channel_layer.group_add(
                self.user_group,
                self.channel_name
            )

        # ৩. হ্যান্ডশেক অ্যাকসেপ্ট করা
        await self.accept()

        # সংযোগ সফল হলে ক্লায়েন্টকে ওয়েলকাম মেসেজ পাঠানো
        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "message": "Connected to MarketPulse AI Live Price Alert WebSocket! 🟢",
            "channels": [self.broadcast_group, self.user_group],
        }))
        logger.info(f"WebSocket client connected to {self.user_group}")

    async def disconnect(self, close_code):
        # গ্রুপ থেকে সংযোগ বিচ্ছিন্ন করা
        if hasattr(self, "broadcast_group"):
            await self.channel_layer.group_discard(
                self.broadcast_group,
                self.channel_name
            )
        if hasattr(self, "user_group") and self.user_group != "anonymous_alerts":
            await self.channel_layer.group_discard(
                self.user_group,
                self.channel_name
            )
        logger.info("WebSocket client disconnected")

    async def receive(self, text_data):
        """
        ক্লায়েন্ট ব্রাউজার থেকে কোনো মেসেজ (যেমন: ping) পাঠালে রেসপন্স দেওয়া
        """
        try:
            data = json.loads(text_data)
            action = data.get("action")
            if action == "ping":
                await self.send(text_data=json.dumps({"action": "pong", "status": "alive"}))
        except Exception as e:
            logger.warning(f"Invalid WebSocket message received: {e}")

    async def price_drop_alert(self, event):
        """
        Channel Layer থেকে আসা প্রাইস ড্রপ অ্যালার্ট ক্লায়েন্টের ব্রাউজারে পুশ করা
        """
        payload = event.get("data", {})
        await self.send(text_data=json.dumps({
            "type": "price_drop_alert",
            "payload": payload,
        }))
