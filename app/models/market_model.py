from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import date, datetime


class MarketBase(BaseModel):
    marketID: int = Field(..., example=1)
    status: str = Field(..., example="open", description="Market status: open or closed")
    openingHours: str = Field(..., example="09:00", description="Market opening time in HH:MM format")
    closingHours: str = Field(..., example="16:00", description="Market closing time in HH:MM format")
    holidays: List[datetime] = Field(
        default_factory=list,
        example=[datetime(2024, 12, 25, 0, 0)],
        description="List of holidays in datetime format"
    )

    @validator("holidays", pre=True, each_item=True)
    def convert_date_to_datetime(cls, v):
        if isinstance(v, date):
            return datetime.combine(v, datetime.min.time())
        return v


class MarketUpdate(BaseModel):
    status: Optional[str] = Field(None, example="closed", description="Market status: open or closed")
    openingHours: Optional[str] = Field(None, example="08:00", description="New opening time in HH:MM format")
    closingHours: Optional[str] = Field(None, example="17:00", description="New closing time in HH:MM format")
    holidays: Optional[List[datetime]] = Field(
        None,
        example=[datetime(2024, 12, 31, 0, 0)],
        description="Updated list of holidays in datetime format"
    )

    @validator("holidays", pre=True, each_item=True)
    def convert_date_to_datetime(cls, v):
        if isinstance(v, date):
            return datetime.combine(v, datetime.min.time())
        return v


class MarketResponse(MarketBase):
    id: str = Field(..., description="Unique identifier for the market in MongoDB")
