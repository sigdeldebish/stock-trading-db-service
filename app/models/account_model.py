from pydantic import BaseModel, Field
from typing import Optional


class AccountBase(BaseModel):
    accountID: int = Field(..., example=1, description="Unique account ID")
    userID: int = Field(..., example=101, description="The customer user ID associated with this account")
    balance: float = Field(..., ge=0.0, example=5000.0, description="Account balance in USD")


class AccountCreate(AccountBase):
    """
    Used when creating a new account.
    Inherits all fields from `AccountBase`.
    """
    pass


class AccountUpdate(BaseModel):
    balance: float = Field(..., ge=0.0, example=1000.0, description="Updated account balance in USD")


class AccountResponse(AccountBase):
    """
    Response model for account data, including the MongoDB Object ID.
    """
    id: str = Field(..., description="MongoDB Object ID for the account")

    class Config:
        from_attributes = True
