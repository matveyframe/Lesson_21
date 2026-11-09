from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from catalog.models import Product
from catalog.schemas import (
    ProductCreate,
    ProductOut,
    StockReserveRequest,
    StockReserveResponse,
)
from common.config import ORDERS_SERVICE_URL, PAYMENTS_SERVICE_URL
from common.database import Base, engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Catalog Service", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "service": "catalog"}


@app.post("/products", response_model=ProductOut, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    product = Product(
        name=payload.name,
        price=payload.price,
        stock=payload.stock,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@app.get("/products", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.scalars(select(Product).order_by(Product.id)).all()


@app.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post("/products/reserve", response_model=StockReserveResponse)
def reserve_stock(payload: StockReserveRequest, db: Session = Depends(get_db)):
    product = db.get(Product, payload.product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.stock < payload.quantity:
        raise HTTPException(
            status_code=409,
            detail=f"Not enough stock: available={product.stock}, requested={payload.quantity}",
        )

    product.stock -= payload.quantity
    db.commit()
    db.refresh(product)

    return StockReserveResponse(
        product_id=product.id,
        quantity=payload.quantity,
        remaining_stock=product.stock,
    )


@app.get("/internal/dependencies")
async def dependencies():
    """Учебный endpoint: показывает HTTP-связность сервисов."""
    results = {}

    async with httpx.AsyncClient(timeout=3) as client:
        for name, url in {
            "orders": f"{ORDERS_SERVICE_URL}/health",
            "payments": f"{PAYMENTS_SERVICE_URL}/health",
        }.items():
            try:
                response = await client.get(url)
                results[name] = response.json()
            except httpx.HTTPError as exc:
                results[name] = {"status": "unavailable", "error": str(exc)}

    return results
