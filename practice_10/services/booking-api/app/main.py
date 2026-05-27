from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
import logging

from .database import engine, Base
from .routers import rooms_router, bookings_router
from .config import config
from .rabbit import init_rabbit, close_rabbit
from .metrics import metrics_middleware, metrics_endpoint
from .schemas import HealthResponse

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание таблиц в БД
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info("Starting booking-api...")
    await init_rabbit(config.RABBITMQ_URL)
    logger.info("Connected to RabbitMQ")
    yield
    # Shutdown
    logger.info("Shutting down booking-api...")
    await close_rabbit()


app = FastAPI(
    title="Booking API",
    description="API for booking meeting rooms",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware для метрик
app.middleware("http")(metrics_middleware)

# Подключение роутеров
app.include_router(rooms_router)
app.include_router(bookings_router)

# Endpoint для метрик Prometheus
app.add_api_route("/metrics", metrics_endpoint, methods=["GET"])


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        services={
            "database": "connected",
            "rabbitmq": "connected"
        }
    )


@app.get("/")
async def root():
    return {
        "service": "booking-api",
        "version": "1.0.0",
        "endpoints": [
            "/rooms",
            "/bookings",
            "/health",
            "/metrics"
        ]
    }
