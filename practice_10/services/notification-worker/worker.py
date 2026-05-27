#!/usr/bin/env python3
"""
Notification Worker — асинхронный обработчик очереди RabbitMQ
Отправляет email и Telegram уведомления о бронированиях
"""

import asyncio
import json
import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any

import aio_pika
import aiohttp
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
QUEUE_NAME = "notifications"

# SMTP настройки
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# Telegram настройки
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


async def send_email(to_email: str, action: str, booking_data: Dict[str, Any]) -> bool:
    """Отправка email уведомления"""
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured, skipping email")
        return False
    
    try:
        room_name = booking_data.get("room_name", "Unknown")
        start_time = booking_data.get("start_time", "")
        end_time = booking_data.get("end_time", "")
        
        if action == "created":
            subject = "✅ Booking Confirmed"
            body = f"""
            Your booking has been confirmed!
            
            Room: {room_name}
            Time: {start_time} - {end_time}
            
            Thank you for using our service!
            """
        elif action == "cancelled":
            subject = "❌ Booking Cancelled"
            body = f"""
            Your booking has been cancelled.
            
            Room: {room_name}
            Time: {start_time} - {end_time}
            
            If you didn't request this, please contact support.
            """
        else:
            subject = "Booking Notification"
            body = f"Booking {action}: {room_name} at {start_time}"
        
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        # Используем синхронный SMTP в отдельном потоке
        loop = asyncio.get_event_loop()
        
        def send():
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
        
        await loop.run_in_executor(None, send)
        logger.info(f"Email sent to {to_email} for booking {booking_data.get('booking_id')}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


async def send_telegram(telegram_id: str, action: str, booking_data: Dict[str, Any]) -> bool:
    """Отправка Telegram уведомления"""
    if not TELEGRAM_BOT_TOKEN or not telegram_id:
        logger.warning("Telegram bot token or user ID not configured")
        return False
    
    try:
        room_name = booking_data.get("room_name", "Unknown")
        start_time = booking_data.get("start_time", "")
        end_time = booking_data.get("end_time", "")
        
        if action == "created":
            text = f"✅ *Booking Confirmed!*\n\nRoom: {room_name}\nTime: {start_time} - {end_time}"
        elif action == "cancelled":
            text = f"❌ *Booking Cancelled*\n\nRoom: {room_name}\nTime: {start_time} - {end_time}"
        else:
            text = f"Booking {action}: {room_name} at {start_time}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                TELEGRAM_API_URL,
                json={
                    "chat_id": telegram_id,
                    "text": text,
                    "parse_mode": "Markdown"
                }
            ) as resp:
                if resp.status == 200:
                    logger.info(f"Telegram message sent to {telegram_id}")
                    return True
                else:
                    logger.error(f"Telegram API error: {await resp.text()}")
                    return False
                    
    except Exception as e:
        logger.error(f"Failed to send Telegram: {e}")
        return False


async def process_message(message: aio_pika.IncomingMessage):
    """Обработка одного сообщения из очереди"""
    async with message.process():
        try:
            data = json.loads(message.body.decode())
            logger.info(f"Processing notification: {data}")
            
            booking_id = data.get("booking_id")
            user_email = data.get("user_email")
            user_telegram_id = data.get("user_telegram_id")
            action = data.get("action", "created")
            booking_data = {
                "room_name": data.get("room_name"),
                "start_time": data.get("start_time"),
                "end_time": data.get("end_time"),
                "booking_id": booking_id
            }
            
            # Отправка уведомлений параллельно
            tasks = []
            
            if user_email:
                tasks.append(send_email(user_email, action, booking_data))
            
            if user_telegram_id:
                tasks.append(send_telegram(user_telegram_id, action, booking_data))
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                success_count = sum(1 for r in results if r is True)
                logger.info(f"Sent {success_count}/{len(tasks)} notifications for booking {booking_id}")
            else:
                logger.warning(f"No notification channels configured for booking {booking_id}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")


async def main():
    """Основная функция worker-а"""
    logger.info("Starting Notification Worker...")
    
    # Подключение к RabbitMQ
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    logger.info(f"Connected to RabbitMQ at {RABBITMQ_URL}")
    
    async with connection:
        channel = await connection.channel()
        
        # Объявление очереди
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)
        logger.info(f"Listening on queue: {QUEUE_NAME}")
        
        # Обработка сообщений
        await queue.consume(process_message)
        
        # Бесконечное ожидание
        try:
            await asyncio.Future()  # Бесконечное ожидание
        except KeyboardInterrupt:
            logger.info("Shutting down...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")