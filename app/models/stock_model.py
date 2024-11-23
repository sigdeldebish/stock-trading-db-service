from pydantic import BaseModel, Field


class StockBase(BaseModel):
    stockID: int = Field(..., example=10)
    stockTicker: str = Field(..., example="AAPL")
    companyName: str = Field(..., example="Apple Inc.")
    volume: int = Field(..., ge=0, example=10000)
    initialPrice: float = Field(..., gt=0, example=150.0)
    currentPrice: float = Field(..., gt=0, example=160.0)
    openingPrice: float = Field(..., gt=0, example=155.0)
    highPrice: float = Field(..., gt=0, example=162.0)
    lowPrice: float = Field(..., gt=0, example=148.0)
    marketStatus: str = Field(..., example="open", description="open or closed")


class StockCreate(StockBase):
    pass


class StockResponse(StockBase):
    id: str = Field(..., description="MongoDB Object ID")
