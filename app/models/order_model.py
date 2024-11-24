from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OrderBase(BaseModel):
    orderID: int = Field(..., example=1001)
    userID: int = Field(..., example=1)
    stockTicker: str = Field(..., example="AAPL", description="Stock ticker symbol")
    orderType: str = Field(..., example="buy", description="buy or sell")
    volume: int = Field(..., ge=1, example=20)
    price: float = Field(..., gt=0, example=160.0)
    status: str = Field(..., example="pending", description="pending, completed, or canceled")
    # timestamp: datetime = Optional[Field(default_factory=datetime.utcnow)]
    marketStatus: str = Field(..., example="open", description="open or closed")


class OrderCreate(OrderBase):
    pass


class OrderResponse(OrderBase):
    id: str = Field(..., description="MongoDB Object ID")
