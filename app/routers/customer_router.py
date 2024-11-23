from fastapi import APIRouter, HTTPException, status, Depends
from app.mongo.connector import db
from app.utils.auth_and_rbac import get_current_user, require_admin_or_self
from bson import ObjectId

router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
    responses={
        403: {"description": "Access forbidden"},
        404: {"description": "Resource not found"},
        400: {"description": "Bad request"},
    },
)


@router.get(
    "/support",
    description="Retrieve support contact details.",
    responses={200: {"description": "Support details retrieved"}},
)
async def get_support_contact_details():
    """
    **Get Support Contact Details:**
    - Returns customer support contact information.
    """
    return {"email": "support@tradingplatform.com", "phone": "+1-800-123-4567"}


@router.post(
    "/validate-bank",
    description="Validate external bank authorization for deposit.",
    responses={
        200: {"description": "Bank authorization validated"},
        400: {"description": "Invalid authorization details"},
    },
)
async def validate_external_bank_authorization_for_deposit(bank_id: str, user=Depends(get_current_user)):
    """
    **Validate External Bank Authorization:**
    - Checks if the provided bank details are valid for deposit.
    """
    if not bank_id or len(bank_id) < 5:
        raise HTTPException(status_code=400, detail="Invalid bank authorization details")

    return {"message": "Bank authorization validated", "bank_id": bank_id}


@router.post(
    "/buy-stock",
    description="Buy stock as a customer.",
    responses={
        200: {"description": "Stock purchased successfully"},
        400: {"description": "Insufficient balance or invalid stock"},
    },
)
async def buy_stock(stock_id: str, volume: int, price: float, user=Depends(get_current_user)):
    """
    **Buy Stock:**
    - Handles stock purchase for the current user.
    """
    total_cost = volume * price

    if user["account"]["balance"] < total_cost:
        raise HTTPException(
            status_code=400, detail="Insufficient balance to complete the purchase"
        )

    stock = await db.stocks.find_one({"_id": ObjectId(stock_id)})
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    # Update user balance and portfolio
    await db.users.update_one(
        {"_id": ObjectId(user["_id"])},
        {
            "$inc": {"account.balance": -total_cost, f"portfolio.{stock_id}": volume},
        },
    )

    # Create transaction record
    transaction = {
        "userID": user["userID"],
        "stockID": stock_id,
        "volume": volume,
        "price": price,
        "totalAmount": total_cost,
        "transactionType": "buy",
    }
    await db.transactions.insert_one(transaction)

    return {"message": "Stock purchased successfully", "transaction": transaction}


@router.post(
    "/sell-stock",
    description="Sell stock as a customer.",
    responses={
        200: {"description": "Stock sold successfully"},
        400: {"description": "Invalid stock or insufficient holdings"},
    },
)
async def sell_stock(stock_id: str, volume: int, price: float, user=Depends(get_current_user)):
    """
    **Sell Stock:**
    - Handles stock sale for the current user.
    """
    if stock_id not in user["portfolio"] or user["portfolio"][stock_id] < volume:
        raise HTTPException(
            status_code=400, detail="Insufficient holdings to complete the sale"
        )

    total_earnings = volume * price

    # Update user portfolio and balance
    await db.users.update_one(
        {"_id": ObjectId(user["_id"])},
        {
            "$inc": {"account.balance": total_earnings, f"portfolio.{stock_id}": -volume},
        },
    )

    # Remove stock from portfolio if quantity is zero
    user = await db.users.find_one({"_id": ObjectId(user["_id"])})
    if user["portfolio"][stock_id] == 0:
        await db.users.update_one(
            {"_id": ObjectId(user["_id"])},
            {"$unset": {f"portfolio.{stock_id}": ""}},
        )

    # Create transaction record
    transaction = {
        "userID": user["userID"],
        "stockID": stock_id,
        "volume": -volume,
        "price": price,
        "totalAmount": total_earnings,
        "transactionType": "sell",
    }
    await db.transactions.insert_one(transaction)

    return {"message": "Stock sold successfully", "transaction": transaction}


@router.post(
    "/deposit-cash",
    description="Deposit cash into the account.",
    responses={
        200: {"description": "Cash deposited successfully"},
        400: {"description": "Invalid deposit amount"},
    },
)
async def deposit_cash(amount: float, user=Depends(get_current_user)):
    """
    **Deposit Cash:**
    - Deposits cash into the user's account.
    """
    if amount <= 0:
        raise HTTPException(
            status_code=400, detail="Deposit amount must be greater than zero"
        )

    await db.users.update_one(
        {"_id": ObjectId(user["_id"])},
        {"$inc": {"account.balance": amount}},
    )

    return {"message": "Cash deposited successfully", "amount": amount}


@router.post(
    "/withdraw-cash",
    description="Withdraw cash from the account.",
    responses={
        200: {"description": "Cash withdrawn successfully"},
        400: {"description": "Insufficient balance or invalid amount"},
    },
)
async def withdraw_cash(amount: float, user=Depends(get_current_user)):
    """
    **Withdraw Cash:**
    - Withdraws cash from the user's account.
    """
    if amount <= 0:
        raise HTTPException(
            status_code=400, detail="Withdrawal amount must be greater than zero"
        )

    if user["account"]["balance"] < amount:
        raise HTTPException(
            status_code=400, detail="Insufficient balance for withdrawal"
        )

    await db.users.update_one(
        {"_id": ObjectId(user["_id"])},
        {"$inc": {"account.balance": -amount}},
    )

    return {"message": "Cash withdrawn successfully", "amount": amount}


@router.get(
    "/portfolio/{user_id}",
    description="Retrieve the user's stock portfolio (self or admin).",
    responses={
        200: {"description": "Portfolio retrieved"},
        404: {"description": "User not found"},
    },
)
async def get_user_portfolio(
    user_id: str, current_user=Depends(require_admin_or_self)
):
    """
    **Get User Portfolio:**
    - Fetches the portfolio of the specified user.
    - Accessible by the user themselves or admin users.
    """
    user = await db.users.find_one({"userID": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "User not found", "code": "USER_NOT_FOUND"},
        )

    portfolio = user.get("portfolio", {})
    return {"portfolio": portfolio}


@router.get(
    "/transactions/{user_id}",
    description="Retrieve the transaction history for a user (self or admin).",
    responses={
        200: {"description": "Transaction history retrieved"},
        404: {"description": "No transactions found"},
    },
)
async def get_transaction_history(
    user_id: str, current_user=Depends(require_admin_or_self)
):
    """
    **Get Transaction History:**
    - Fetches the transaction history for the specified user.
    - Accessible by the user themselves or admin users.
    """
    transactions = await db.transactions.find({"userID": user_id}).to_list(length=50)
    if not transactions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "No transactions found", "code": "TRANSACTIONS_NOT_FOUND"},
        )

    for txn in transactions:
        txn["id"] = str(txn["_id"])
        del txn["_id"]

    return {"transactions": transactions}
