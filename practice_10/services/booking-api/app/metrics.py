from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time
from fastapi import Request

# Метрики
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

bookings_created_total = Counter(
    'bookings_created_total',
    'Total bookings created'
)

rooms_created_total = Counter(
    'rooms_created_total',
    'Total rooms created'
)


async def metrics_middleware(request: Request, call_next):
    """Middleware для сбора метрик HTTP запросов"""
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    endpoint = request.url.path

    http_requests_total.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=response.status_code
    ).inc()

    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=endpoint
    ).observe(duration)

    return response


async def metrics_endpoint(request: Request):
    """Endpoint для сбора метрик Prometheus"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
