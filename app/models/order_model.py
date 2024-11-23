from pydantic import BaseModel, Field
from datetime import datetime


class OrderBase(BaseModel):
    orderID: int = Field(..., example=1001)
    userID: int = Field(..., example=1)
    stockID: int = Field(..., example=10)
    orderType: str = Field(..., example="buy", description="buy or sell")
    volume: int = Field(..., ge=1, example=20)
    price: float = Field(..., gt=0, example=160.0)
    status: str = Field(..., example="pending", description="pending, completed, or canceled")
    timestamp: datetime = Field(default_factory=datetime.utcnow, example="2024-11-24T12:34:56Z")
    marketStatus: str = Field(..., example="open", description="open or closed")


class OrderCreate(OrderBase):
    pass


class OrderResponse(OrderBase):
    id: str = Field(..., description="MongoDB Object ID")
