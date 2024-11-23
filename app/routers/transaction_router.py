from fastapi import APIRouter, HTTPException, status, Depends
from app.models.transaction_model import TransactionCreate, TransactionResponse
from app.mongo.connector import db
from bson import ObjectId
from app.utils.auth_and_rbac import get_current_user, require_admin_or_self

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
    responses={
        404: {"description": "Transaction not found"},
        400: {"description": "Bad request"},
        403: {"description": "Forbidden"},
    },
)


@router.post(
    "/",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    description="Create a new transaction for a completed order (admin or self).",
    responses={
        201: {"description": "Transaction created successfully"},
        400: {"description": "Invalid transaction data"},
        403: {"description": "Access denied"},
    },
)
async def create_transaction(transaction: TransactionCreate, user=Depends(get_current_user)):
    """
    **Create Transaction:**
    - Records a new transaction for a completed order.
    - Only accessible by admins or the order's associated user.
    """
    # Validate the transaction's user ownership or admin rights
    if user["userType"] != "admin" and transaction.userID != user["userID"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Access denied", "code": "ACCESS_DENIED"},
        )

    transaction_data = transaction.dict()

    # Insert the new transaction
    result = await db.transactions.insert_one(transaction_data)
    transaction_data["id"] = str(result.inserted_id)

    return transaction_data


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
    description="Retrieve transaction details by ID (admin or self).",
    responses={
        200: {"description": "Transaction retrieved successfully"},
        404: {"description": "Transaction not found"},
        403: {"description": "Access denied"},
    },
)
async def get_transaction(transaction_id: str, user=Depends(require_admin_or_self)):
    """
    **Get Transaction Details:**
    - Fetches details of a transaction by its unique ID.
    - Accessible by admins or the transaction's associated user.
    """
    transaction = await db.transactions.find_one({"_id": ObjectId(transaction_id)})

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Transaction not found", "code": "TRANSACTION_NOT_FOUND"},
        )

    # Validate user access to this transaction
    if user["userType"] != "admin" and transaction["userID"] != user["userID"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Access denied", "code": "ACCESS_DENIED"},
        )

    transaction["id"] = str(transaction["_id"])
    del transaction["_id"]
    return transaction
