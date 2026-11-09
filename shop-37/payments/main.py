import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from common.database import Base, engine, get_db
from payments.models import Payment, PaymentStatus
from payments.schemas import PaymentCreate, PaymentOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Payments Service", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "service": "payments"}


@app.post("/payments", response_model=PaymentOut, status_code=201)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
    payment = Payment(
        order_id=payload.order_id,
        amount=payload.amount,
        status=PaymentStatus.paid,
        transaction_id=f"txn_{uuid.uuid4().hex}",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@app.get("/payments", response_model=list[PaymentOut])
def list_payments(db: Session = Depends(get_db)):
    return db.scalars(select(Payment).order_by(Payment.created_at)).all()


@app.get("/payments/{payment_id}", response_model=PaymentOut)
def get_payment(payment_id: uuid.UUID, db: Session = Depends(get_db)):
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment
