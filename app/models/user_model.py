from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict


class Account(BaseModel):
	accountID: Optional[int] = Field(None, example=101, description="Unique account ID for the user")
	balance: float = Field(..., ge=0.0, example=5000.0, description="Balance in the user's account")


class UserSignup(BaseModel):
	username: str = Field(..., example="johndoe", description="Unique username for the user")
	email: EmailStr = Field(..., example="john@example.com", description="Email address of the user")
	password: str = Field(..., min_length=8, example="password123", description="User's password")
	userType: str = Field(..., example="customer", description="User type: 'customer' or 'admin'")


class UserDetailUpdate(BaseModel):
	email: EmailStr = Field(..., example="john@example.com", description="Email address of the user")
	userType: str = Field(..., example="customer", description="User type: 'customer' or 'admin'")


class UserBase(BaseModel):
	userID: int = Field(..., example=1, description="Unique user ID")
	username: str = Field(..., example="johndoe", description="Unique username for the user")
	email: EmailStr = Field(..., example="john@example.com", description="User's email address")
	userType: str = Field(..., example="customer", description="User type: 'customer' or 'admin'")


class CustomerUser(UserBase):
	account: Optional[Account] = Field(
		None, description="Account details for the customer user"
	)
	portfolio: Optional[Dict[int, int]] = Field(
		default_factory=dict,
		example={10: 50},
		description="Customer's stock portfolio (stockID: number of shares)",
	)


class AdminUser(UserBase):
	pass  # Admins do not have an account or portfolio


class UserResponse(BaseModel):
	username: str = Field(..., example="johndoe", description="Unique username for the user")
	email: str = Field(..., example="john@example.com", description="Email address of the user")
	userType: str = Field(..., example="customer", description="User type: 'customer' or 'admin'")
	account: Optional[Account] = Field(
		None,
		description="Account details if the user is a customer. Not applicable for admin users.",
	)
	portfolio: Optional[Dict[int, int]] = Field(
		default_factory=dict,
		description="Customer's stock portfolio (stockID: volume). Not applicable for admin users.",
	)

	class Config:
		from_attributes = True
