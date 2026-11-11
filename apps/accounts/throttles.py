from rest_framework.throttling import UserRateThrottle


class TierBasedUserRateThrottle(UserRateThrottle):
    THROTTLE_RATES = {
        "admin": None,
        "enterprise": "300/min",
        "pro": "60/min",
        "free": "10/min",
    }

    def __init__(self):
        self.rate = "10/min"
        super().__init__()

    def allow_request(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            self.rate = "10/min"
        elif user.is_staff or getattr(user, "role", "") == "ADMIN":
            return True
        else:
            role = str(getattr(user, "role", "FREE")).lower()
            self.rate = self.THROTTLE_RATES.get(role, "10/min")

        self.num_requests, self.duration = self.parse_rate(self.rate)
        return super().allow_request(request, view)