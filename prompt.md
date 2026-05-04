# Промт для ИИ-ассистента (для выполнения практических работ)

## Контекст проекта
- **Тема:** API для бронирования переговорных комнат
- **Студент:** Борисов Артём Игоревич, группа ИКМО-01-25
- **Цель:** Повышенный балл (+10)
- **Технологии:** Python, Flask, SQLAlchemy, PostgreSQL, RabbitMQ, aiogram, Docker, Minikube, Linkerd, Prometheus, Grafana, Jaeger, Loki
- **Окружение:** Windows + WSL, PostgreSQL в Docker, Minikube (драйвер Docker)

## Архитектура (микросервисы)
1. **booking-api** (Flask + SQLAlchemy) — API Gateway, бизнес-логика бронирования
2. **notification-worker** (asyncio + aiosmtplib + aiogram + pika) — отправка email и Telegram через RabbitMQ
3. **frontend** (Flask + Bootstrap) — веб-интерфейс для пользователей и админов
4. **PostgreSQL** — БД (StatefulSet + PVC в K8s)
5. **RabbitMQ** — очередь сообщений между booking-api и notification-worker
6. **SMTP** — внешний сервис для email (из Практики №3)
7. **Telegram Bot API** — внешний сервис (библиотека aiogram)

## Требования к коду
- Взаимодействие между booking-api и notification-worker **только через RabbitMQ** (не HTTP)
- Email отправляется через код из Практики №3 (адаптированный под asyncio или threading)
- Telegram — через aiogram (асинхронный)
- SQLAlchemy (синхронный режим) + PostgreSQL
- Dockerfile для каждого сервиса
- docker-compose.yml для локальной разработки
- Автотесты (pytest, минимум 5 сценариев)
- В коде должны быть эндпоинты для метрик Prometheus (/metrics)

## Требования к K8s (повышенный балл)
- StatefulSet + PVC для PostgreSQL
- Deployment + Service для booking-api, notification-worker, frontend, RabbitMQ
- Ingress для frontend и booking-api
- ConfigMap + Secret (пароли БД, токен Telegram)
- Service Mesh: Linkerd (аннотации в Deployment)
- Jaeger (распределённая трассировка) — интеграция через OpenTelemetry
- Loki + Promtail (централизованный сбор логов)

## Требования к мониторингу
- Prometheus + Grafana (установка через helm)
- Кастомные метрики приложения:
  - `bookings_created_total` (счётчик)
  - `bookings_duration_seconds` (гистограмма)
  - `notifications_sent_total` (по типу email/telegram)
  - `rabbitmq_queue_length` (размер очереди)
- Дашборд в Grafana (минимум 4 панели)

## Структура репозитория (предварительно на момент создания промта)
```
practice_9-12/
├── practice_9/
│   ├── diagrams/
│   │   ├── context.puml
│   │   ├── container.puml
│   │   └── component.puml
│   └── README.md
├── practice_10/
│   ├── services/
│   │   ├── booking-api/
│   │   │   ├── app.py
│   │   │   ├── models.py
│   │   │   ├── requirements.txt
│   │   │   └── Dockerfile
│   │   ├── notification-worker/
│   │   │   ├── worker.py
│   │   │   ├── email_sender.py (из Практики 3)
│   │   │   ├── telegram_bot.py
│   │   │   ├── requirements.txt
│   │   │   └── Dockerfile
│   │   └── frontend/
│   │       ├── app.py
│   │       ├── templates/
│   │       ├── static/
│   │       ├── requirements.txt
│   │       └── Dockerfile
│   ├── tests/
│   │   └── test_api.py
│   ├── docker-compose.yml
│   └── PRACTICE2.md
├── practice_11/
│   ├── k8s/
│   │   ├── namespace.yaml
│   │   ├── configmap.yaml
│   │   ├── secret.yaml
│   │   ├── postgres-statefulset.yaml
│   │   ├── rabbitmq-deployment.yaml
│   │   ├── booking-api-deployment.yaml
│   │   ├── notification-worker-deployment.yaml
│   │   ├── frontend-deployment.yaml
│   │   ├── services.yaml
│   │   ├── ingress.yaml
│   │   └── linkerd-annotations.yaml
│   └── PRACTICE3.md
├── practice_12/
│   ├── monitoring/
│   │   ├── prometheus-values.yaml
│   │   ├── grafana-dashboard.json
│   │   ├── loki-values.yaml
│   │   └── jaeger-values.yaml
│   ├── screenshots/
│   └── PRACTICE4.md
└── README.md
```

## Задание для ИИ (что нужно сгенерировать)

### Для практики №1
- Problem Statement (в соответствии с архитектурой выше)
- Диаграмма C1 (контекст) в PlantUML
- Диаграмма C2 (контейнеры) в PlantUML
- Диаграмма C3 (компоненты для booking-api) в PlantUML

### Для практики №2
- Полный код booking-api (Flask + SQLAlchemy + RabbitMQ publisher)
- Полный код notification-worker (pika consumer + aiosmtplib + aiogram)
- Полный код frontend (Flask + Bootstrap)
- Код адаптированного email_sender из Практики №3
- Код Telegram-бота на aiogram (получение chat_id, отправка сообщений)
- docker-compose.yml (postgres, rabbitmq, booking-api, notification-worker, frontend)
- pytest (5 тестов: создание брони, конфликт, отмена, список комнат, проверка очереди)
- README с инструкцией по запуску

### Для практики №3
- Dockerfile для каждого сервиса
- Все YAML-манифесты (Deployment, Service, Ingress, StatefulSet, ConfigMap, Secret)
- Инструкция по установке Linkerd
- Инструкция по деплою в Minikube

### Для практики №4
- Конфигурация Prometheus + ServiceMonitor
- Кастомные метрики в коде (/metrics)
- Дашборд Grafana (JSON)
- Установка Jaeger + OpenTelemetry instrumentation
- Установка Loki + Promtail
- Инструкция по настройке мониторинга

## Формат ответа от ИИ
Каждое задание выводить в отдельном сообщении с указанием названия файла. Код должен быть готов к копированию и запуску. Комментарии на русском языке (ключевые моменты).

## Текущий запрос
[Здесь я напишу, что именно нужно сгенерировать]