from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    price: float = Field(gt=0)
    stock: int = Field(ge=0)


class ProductOut(BaseModel):
    id: int
    name: str
    price: float
    stock: int

    class Config:
        from_attributes = True


class StockReserveRequest(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class StockReserveResponse(BaseModel):
    product_id: int
    quantity: int
    remaining_stock: int
