import time
import logging

logger = logging.getLogger(__name__)

class ExecutionTimeLoggingMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration_ms = (time.time() - start_time) * 1000
        formatted_time = f"{duration_ms:.2f} ms"
        response['X-Execution-Time'] = formatted_time

        print(f"[{request.method}] {request.path} -> Duration: {formatted_time}")

        return response