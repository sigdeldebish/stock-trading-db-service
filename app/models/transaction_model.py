from pydantic import BaseModel, Field
from datetime import datetime


class TransactionBase(BaseModel):
    orderID: int = Field(..., example=1001, description="The ID of the order associated with the transaction")
    username: str = Field(..., example="johndoe", description="The username of the user making the transaction")
    stockTicker: str = Field(..., example="AAPL", description="Ticker of the stock being transacted")
    volume: int = Field(..., ge=1, example=20, description="Number of shares involved in the transaction")
    price: float = Field(..., gt=0, example=160.0, description="Price per share during the transaction")
    totalPrice: float = Field(..., gt=0, example=3200.0, description="Total value of the transaction (volume * price)")
    transactionDate: datetime = Field(
        default_factory=datetime.utcnow,
        example="2024-11-24T12:34:56Z",
        description="Date and time of the transaction",
    )


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(TransactionBase):
    id: str = Field(..., description="MongoDB Object ID for the transaction")

    class Config:
        from_attributes = True
