from pydantic import BaseModel, Field


class StockBase(BaseModel):
    stockTicker: str = Field(..., example="AAPL", description="Stock ticker symbol")
    companyName: str = Field(..., example="Apple Inc.")
    volume: int = Field(..., ge=0, example=10000)
    initialPrice: float = Field(..., ge=0)
    currentPrice: float = Field(..., ge=0)
    openingPrice: float = Field(..., ge=0)
    highPrice: float = Field(..., ge=0)
    lowPrice: float = Field(..., ge=0)
    marketStatus: str = Field(..., example="open", description="open or closed")


class StockCreate(StockBase):
    stockID: str = Field(None, example="unique-stock-id", description="Unique stock ID (optional, generated if not provided)")


class StockResponse(StockBase):
    id: str = Field(..., description="MongoDB Object ID")

class StockUpdateRequest(BaseModel):
    stock_ticker: str = Field(..., description="The ticker symbol of the stock")
    price: float = Field(..., gt=0, description="The new price of the stock")