import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    order_id: int
    amount: Decimal = Field(gt=0)


class PaymentOut(BaseModel):
    id: uuid.UUID
    order_id: int
    amount: Decimal
    status: str
    transaction_id: str

    class Config:
        from_attributes = True
