from decimal import Decimal

from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=200)
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    customer_name: str
    status: str
    total_amount: Decimal
    payment_id: str | None
    items: list[OrderItemOut]

    class Config:
        from_attributes = True
