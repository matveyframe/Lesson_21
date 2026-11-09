import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://shop_user:shop_password@localhost:5432/shop_db",
)

CATALOG_SERVICE_URL = os.getenv("CATALOG_SERVICE_URL", "http://127.0.0.1:8001")
ORDERS_SERVICE_URL = os.getenv("ORDERS_SERVICE_URL", "http://127.0.0.1:8002")
PAYMENTS_SERVICE_URL = os.getenv("PAYMENTS_SERVICE_URL", "http://127.0.0.1:8003")
