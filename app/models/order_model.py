from pydantic import BaseModel, Field, root_validator
from typing import Optional
from datetime import datetime
import uuid


class OrderBase(BaseModel):
	username: str = Field(..., example="johndoe", description="Username of the user placing the order")
	stockTicker: str = Field(..., example="AAPL", description="Stock ticker symbol")
	orderType: str = Field(..., example="buy", description="Type of order: 'buy' or 'sell'")
	volume: int = Field(..., ge=1, example=20, description="Number of shares in the order")
	status: str = Field(
		default="pending", example="pending", description="Order status: 'pending', 'completed', or 'canceled'"
	)
	marketStatus: str = Field(..., example="open", description="Market status: 'open' or 'closed'")
	order_total: Optional[float] = Field(
		None, gt=0, example=3200.0, description="Total value of the order (calculated as volume * current price)"
	)


class OrderCreate(BaseModel):
	username: str = Field(..., example="johndoe", description="Username of the user placing the order")
	stockTicker: str = Field(..., example="AAPL", description="Stock ticker symbol")
	orderType: str = Field(..., example="buy", description="Type of order: 'buy' or 'sell'")
	volume: int = Field(..., ge=1, example=20, description="Number of shares in the order")
	status: str = Field(
		default="pending", example="pending", description="Order status: 'pending', 'completed', or 'canceled'"
	)
	marketStatus: str = Field(..., example="open", description="Market status: 'open' or 'closed'")
	orderID: Optional[int] = Field(None, example=1001, description="Unique order ID, generated if not provided")

	@root_validator(pre=True)
	def generate_order_id_if_missing(cls, values):
		"""
        Automatically generate an `orderID` if it is not provided.
        """
		if "orderID" not in values or values["orderID"] is None:
			values["orderID"] = int(uuid.uuid4().int >> 64)  # Generate a unique 64-bit integer
		return values


class OrderResponse(OrderBase):
	id: str = Field(..., description="MongoDB Object ID for the order")


class BuyStockRequest(BaseModel):
	stock_ticker: str = Field(..., example="AAPL", description="Stock ticker symbol")
	volume: int = Field(..., example=10, description="Number of shares to purchase")


class SellStockRequest(BaseModel):
	stock_ticker: str = Field(..., example="AAPL", description="Stock ticker symbol")
	volume: int = Field(..., gt=0, example=10, description="Number of shares to sell")

