# core/middleware/performance_middleware.py

import time
import logging

logger = logging.getLogger("performance")

class PerformanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        duration = time.perf_counter() - start

        logger.info(f"{request.method} {request.path} - {duration:.4f} segundos")
        return response
