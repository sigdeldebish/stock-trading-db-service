from pydantic import BaseModel, Field
from datetime import datetime


class TransactionBase(BaseModel):
    transactionID: int = Field(..., example=2001)
    orderID: int = Field(..., example=1001)
    userID: int = Field(..., example=1)
    stockID: int = Field(..., example=10)
    volume: int = Field(..., ge=1, example=20)
    price: float = Field(..., gt=0, example=160.0)
    totalAmount: float = Field(..., gt=0, example=3200.0)
    transactionDate: datetime = Field(default_factory=datetime.utcnow, example="2024-11-24T12:34:56Z")


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(TransactionBase):
    id: str = Field(..., description="MongoDB Object ID")
