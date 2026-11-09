# Shop Demo API

Учебное приложение, имитирующее API интернет-магазина.

Приложение состоит из трёх независимых Python-сервисов, которые запускаются отдельными процессами и общаются по HTTP:

- **Catalog Service** (`:8001`) — товары и складские остатки.
- **Orders Service** (`:8002`) — заказы; вызывает Catalog и Payments.
- **Payments Service** (`:8003`) — платежи.

Данные хранятся в PostgreSQL.

## Архитектура

```text
curl / клиент
   │
   ▼
Orders Service :8002
   ├── HTTP → Catalog Service :8001
   └── HTTP → Payments Service :8003

Catalog Service :8001 ──┐
Orders Service :8002 ───┼── PostgreSQL
Payments Service :8003 ─┘
```

## Запуск

### Catalog Service

```bash
uvicorn catalog.main:app --host 127.0.0.1 --port 8001 --reload
```

### Payments Service

```bash
uvicorn payments.main:app --host 127.0.0.1 --port 8003 --reload
```

### Orders Service

```bash
uvicorn orders.main:app --host 127.0.0.1 --port 8002 --reload
```

Схемы таблиц создаются автоматически при старте каждого сервиса.
## Проверка

```bash
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8002/health
curl http://127.0.0.1:8003/health
```

Создание товара:

```bash
curl -X POST http://127.0.0.1:8001/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Mechanical Keyboard", "price": 120.50, "stock": 10}'
```

Создание заказа:

```bash
curl -X POST http://127.0.0.1:8002/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Anastasia",
    "items": [
      {"product_id": 1, "quantity": 2}
    ]
  }'
```

Просмотр заказов:

```bash
curl http://127.0.0.1:8002/orders
```

Просмотр платежей:

```bash
curl http://127.0.0.1:8003/payments
```

## HTTP API

### Catalog Service

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/products` | Создать товар |
| `GET` | `/products` | Список товаров |
| `GET` | `/products/{id}` | Получить товар |
| `POST` | `/products/reserve` | Уменьшить остаток |
| `GET` | `/internal/dependencies` | Проверка доступности других сервисов |

### Orders Service

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/orders` | Создать заказ |
| `GET` | `/orders` | Список заказов |
| `GET` | `/orders/{id}` | Получить заказ |

### Payments Service

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/payments` | Создать платеж |
| `GET` | `/payments` | Список платежей |
| `GET` | `/payments/{id}` | Получить платеж |

## Логика заказа

1. Клиент отправляет `POST /orders` в Orders Service.
2. Orders Service получает данные каждого товара из Catalog Service по HTTP.
3. Orders Service резервирует остаток через `POST /products/reserve`.
4. Orders Service создаёт платёж через Payments Service.
5. При успехе заказ получает статус `paid`, иначе — `failed`.
