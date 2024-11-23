from fastapi import APIRouter, HTTPException, status, Depends
from app.models.account_model import AccountCreate, AccountResponse
from app.mongo.connector import db
from app.utils.auth_and_rbac import require_admin_or_self, get_current_user
from bson import ObjectId

router = APIRouter(
    prefix="/accounts",
    tags=["Accounts"],
    responses={
        403: {"description": "Forbidden"},
        404: {"description": "Account not found"},
        400: {"description": "Bad request"},
    },
)


@router.post(
    "/",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    description="Create a new account for a customer (admin only).",
    responses={
        201: {"description": "Account created successfully"},
        400: {"description": "Account already exists or user is not a customer"},
    },
)
async def create_account(account: AccountCreate, current_user=Depends(get_current_user)):
    """
    **Create Account:**
    - Creates a new account for a customer.
    - Admin-only operation.
    """
    user = await db.users.find_one({"userID": account.userID})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "User not found", "code": "USER_NOT_FOUND"},
        )
    if user["userType"] != "customer":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Only customer users can have accounts", "code": "INVALID_USER_TYPE"},
        )
    existing_account = await db.accounts.find_one({"userID": account.userID})
    if existing_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Account already exists for this user", "code": "ACCOUNT_EXISTS"},
        )

    account_data = account.dict()
    result = await db.accounts.insert_one(account_data)
    account_data["id"] = str(result.inserted_id)

    # Link the account to the user
    await db.users.update_one(
        {"userID": account.userID}, {"$set": {"accountID": account.accountID}}
    )

    return account_data


@router.get(
    "/{account_id}",
    response_model=AccountResponse,
    status_code=status.HTTP_200_OK,
    description="Retrieve account details by account ID (admin or self).",
)
async def get_account(account_id: str, current_user=Depends(require_admin_or_self)):
    """
    **Get Account Details:**
    - Fetches account details for the given account ID.
    - Accessible by admin users or the account owner.
    """
    account = await db.accounts.find_one({"_id": ObjectId(account_id)})
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Account not found", "code": "ACCOUNT_NOT_FOUND"},
        )
    account["id"] = str(account["_id"])
    del account["_id"]
    return account


@router.put(
    "/{account_id}",
    response_model=AccountResponse,
    status_code=status.HTTP_200_OK,
    description="Update account balance (admin or self).",
    responses={
        200: {"description": "Account balance updated successfully"},
        404: {"description": "Account not found"},
        400: {"description": "Invalid balance value"},
    },
)
async def update_account_balance(
    account_id: str,
    balance: float,
    current_user=Depends(require_admin_or_self),
):
    """
    **Update Account Balance:**
    - Updates the balance of the specified account.
    - Accessible by admin users or the account owner.
    """
    if balance < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Balance cannot be negative", "code": "INVALID_BALANCE"},
        )

    result = await db.accounts.update_one(
        {"_id": ObjectId(account_id)}, {"$set": {"balance": balance}}
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Account not found", "code": "ACCOUNT_NOT_FOUND"},
        )

    updated_account = await db.accounts.find_one({"_id": ObjectId(account_id)})
    updated_account["id"] = str(updated_account["_id"])
    del updated_account["_id"]
    return updated_account
