from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class MarketBase(BaseModel):
    marketID: int = Field(..., example=1)
    status: str = Field(..., example="open", description="open or closed")
    openingHours: str = Field(..., example="09:00")
    closingHours: str = Field(..., example="16:00")
    holidays: List[date] = Field(..., example=["2024-12-25"])


class MarketUpdate(BaseModel):
    status: Optional[str] = Field(None, example="closed")
    openingHours: Optional[str] = Field(None, example="08:00")
    closingHours: Optional[str] = Field(None, example="17:00")
    holidays: Optional[List[date]] = Field(None, example=["2024-12-31"])


class MarketResponse(MarketBase):
    id: str = Field(..., description="MongoDB Object ID")
