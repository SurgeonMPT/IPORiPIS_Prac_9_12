import json
import logging
from typing import Dict, Any

import aio_pika

logger = logging.getLogger(__name__)


class RabbitMQClient:
    def __init__(self, url: str):
        self.url = url
        self.connection = None
        self.channel = None

    async def connect(self):
        """Подключение к RabbitMQ"""
        self.connection = await aio_pika.connect_robust(self.url)
        self.channel = await self.connection.channel()
        # Объявляем очередь
        await self.channel.declare_queue("notifications", durable=True)
        logger.info("Connected to RabbitMQ")

    async def publish_notification(self, data: Dict[str, Any]):
        """Публикация уведомления в очередь"""
        if not self.channel:
            await self.connect()

        message = aio_pika.Message(
            body=json.dumps(data).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )

        await self.channel.default_exchange.publish(
            message,
            routing_key="notifications"
        )
        logger.info(f"Published notification: {data.get('booking_id')}")

    async def close(self):
        """Закрытие соединения"""
        if self.connection:
            await self.connection.close()


rabbit_client = None


async def get_rabbit():
    global rabbit_client
    return rabbit_client


async def init_rabbit(rabbitmq_url: str):
    global rabbit_client
    rabbit_client = RabbitMQClient(rabbitmq_url)
    await rabbit_client.connect()
    return rabbit_client


async def close_rabbit():
    if rabbit_client:
        await rabbit_client.close()
