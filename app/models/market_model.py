from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import date, datetime


class MarketBase(BaseModel):
	marketID: int = Field(..., example=1)
	status: str = Field(..., example="open", description="Market status: open or closed")
	openingHours: str = Field(..., example="09:00", description="Market opening time in HH:MM format")
	closingHours: str = Field(..., example="16:00", description="Market closing time in HH:MM format")
	holidays: List[date] = Field(default_factory=list, example=[date(2024, 12, 25)], description="List of holidays")


class MarketUpdate(BaseModel):
	status: Optional[str] = Field(None, example="closed", description="Market status: open or closed")
	openingHours: Optional[str] = Field(None, example="08:00", description="New opening time in HH:MM format")
	closingHours: Optional[str] = Field(None, example="17:00", description="New closing time in HH:MM format")
	holidays: Optional[List[date]] = Field(None, example=[date(2024, 12, 31)], description="Updated list of holidays")


class MarketResponse(MarketBase):
	id: str = Field(..., description="Unique identifier for the market in MongoDB")
