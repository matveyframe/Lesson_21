from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from common.config import CATALOG_SERVICE_URL, PAYMENTS_SERVICE_URL
from common.database import Base, engine, get_db
from orders.models import Order, OrderItem, OrderStatus
from orders.schemas import OrderCreate, OrderOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Orders Service", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "service": "orders"}


@app.get("/orders", response_model=list[OrderOut])
def list_orders(db: Session = Depends(get_db)):
    return db.scalars(select(Order).order_by(Order.id)).all()


@app.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.post("/orders", response_model=OrderOut, status_code=201)
async def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    order = Order(
        customer_name=payload.customer_name,
        status=OrderStatus.created,
        total_amount=0,
    )
    db.add(order)
    db.flush()

    total = 0.0

    async with httpx.AsyncClient(timeout=5) as client:
        for item in payload.items:
            try:
                product_response = await client.get(
                    f"{CATALOG_SERVICE_URL}/products/{item.product_id}"
                )
            except httpx.HTTPError as exc:
                db.rollback()
                raise HTTPException(
                    status_code=503,
                    detail=f"Catalog service unavailable: {exc}",
                )

            if product_response.status_code == 404:
                db.rollback()
                raise HTTPException(
                    status_code=404,
                    detail=f"Product {item.product_id} not found",
                )
            if product_response.status_code != 200:
                db.rollback()
                raise HTTPException(
                    status_code=502,
                    detail="Unexpected response from Catalog service",
                )

            product = product_response.json()

            try:
                reserve_response = await client.post(
                    f"{CATALOG_SERVICE_URL}/products/reserve",
                    json={
                        "product_id": item.product_id,
                        "quantity": item.quantity,
                    },
                )
            except httpx.HTTPError as exc:
                db.rollback()
                raise HTTPException(
                    status_code=503,
                    detail=f"Catalog service unavailable: {exc}",
                )

            if reserve_response.status_code == 409:
                db.rollback()
                raise HTTPException(
                    status_code=409,
                    detail=reserve_response.json().get("detail", "Not enough stock"),
                )
            if reserve_response.status_code != 200:
                db.rollback()
                raise HTTPException(
                    status_code=502,
                    detail="Failed to reserve stock",
                )

            unit_price = float(product["price"])
            total += unit_price * item.quantity

            db.add(
                OrderItem(
                    order_id=order.id,
                    product_id=item.product_id,
                    product_name=product["name"],
                    quantity=item.quantity,
                    unit_price=unit_price,
                )
            )

    order.total_amount = total

    try:
        payment_response = await client.post(
            f"{PAYMENTS_SERVICE_URL}/payments",
            json={
                "order_id": order.id,
                "amount": total,
            },
        )
    except httpx.HTTPError as exc:
        order.status = OrderStatus.failed
        db.commit()
        raise HTTPException(
            status_code=503,
            detail=f"Payment service unavailable: {exc}",
        )

    if payment_response.status_code != 201:
        order.status = OrderStatus.failed
        db.commit()
        raise HTTPException(
            status_code=502,
            detail="Payment failed",
        )

    payment = payment_response.json()
    order.status = OrderStatus.paid
    order.payment_id = payment["transaction_id"]

    db.commit()
    db.refresh(order)
    return order
