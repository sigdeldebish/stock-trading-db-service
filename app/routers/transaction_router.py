from fastapi import APIRouter, HTTPException, status, Depends, Query
from app.models.transaction_model import TransactionCreate, TransactionResponse
from app.mongo.connector import db
from bson import ObjectId
from app.utils.auth_and_rbac import get_current_user

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions Operations"],
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
    description="Create a new transaction for a completed order.",
    responses={
        201: {"description": "Transaction created successfully"},
        400: {"description": "Invalid transaction data"},
    },
)
async def create_transaction(transaction: TransactionCreate, user=Depends(get_current_user)):
    """
    **Create Transaction:**
    - Records a new transaction for a completed order.
    - Only accessible by the logged-in user or admins.
    """
    # Validate transaction user ownership
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
    description="Retrieve transaction details by ID.",
    responses={
        200: {"description": "Transaction retrieved successfully"},
        404: {"description": "Transaction not found"},
    },
)
async def get_transaction(transaction_id: str, user=Depends(get_current_user)):
    """
    **Get Transaction Details:**
    - Fetches details of a transaction by its unique ID.
    - Accessible by the logged-in user or admins.
    """
    transaction = await db.transactions.find_one({"_id": ObjectId(transaction_id)})

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Transaction not found", "code": "TRANSACTION_NOT_FOUND"},
        )

    # Validate access
    if user["userType"] != "admin" and transaction["userID"] != user["userID"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Access denied", "code": "ACCESS_DENIED"},
        )

    transaction["id"] = str(transaction["_id"])
    del transaction["_id"]
    return transaction


@router.get(
    "/self",
    response_model=list[TransactionResponse],
    status_code=status.HTTP_200_OK,
    description="Retrieve all transactions for the logged-in user, or the latest one if specified.",
    responses={
        200: {"description": "Transactions retrieved successfully"},
    },
)
async def get_transactions_for_user(
    latest: bool = Query(False, description="Set to true to retrieve only the latest transaction"),
    user=Depends(get_current_user),
):
    """
    **Get Transactions for User:**
    - Retrieves all transactions for the logged-in user.
    - If `latest` is true, retrieves only the most recent transaction.
    """
    query = {"userID": user["userID"]}
    transactions = await db.transactions.find(query).sort("timestamp", -1).to_list(None)

    if not transactions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "No transactions found for this user", "code": "NO_TRANSACTIONS"},
        )

    if latest:
        return [transactions[0]]  # Return only the most recent transaction

    for transaction in transactions:
        transaction["id"] = str(transaction["_id"])
        del transaction["_id"]

    return transactions
