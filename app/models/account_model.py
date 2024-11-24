from pydantic import BaseModel, Field


class AccountBase(BaseModel):
    balance: float = Field(
        0.0, ge=0.0, example=5000.0, description="Balance in the user's account"
    )


class AccountCreate(AccountBase):
    username: str = Field(..., example="johndoe", description="Username of the customer for whom the account is created")


class AccountResponse(AccountBase):
    username: str = Field(..., example="johndoe", description="Username of the account holder")
    id: str = Field(..., description="MongoDB Object ID for the account")

    class Config:
        from_attributes = True
