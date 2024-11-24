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
    """Provides customer support contact information."""
    return {"email": "support@tradingplatform.com", "phone": "+1-800-123-4567"}


@router.post(
    "/validate-bank",
    description="Validate external bank authorization for deposit.",
    responses={200: {"description": "Bank authorization validated"}},
)
async def validate_external_bank_authorization_for_deposit(bank_id: str, user=Depends(get_current_user)):
    """
    Validates external bank details for deposit.
    """
    if not bank_id or len(bank_id) < 5:
        raise HTTPException(status_code=400, detail="Invalid bank authorization details")

    return {"message": "Bank authorization validated", "bank_id": bank_id}


@router.post(
    "/buy-stock",
    description="Buy stock as a customer.",
    responses={200: {"description": "Stock purchased successfully"}},
)
async def buy_stock(stock_ticker: str, volume: int, price: float, order_id: str, user=Depends(get_current_user)):
    """
    Buys stock for the authenticated user and records a transaction.
    """
    total_cost = volume * price

    if user["account"]["balance"] < total_cost:
        raise HTTPException(
            status_code=400, detail="Insufficient balance to complete the purchase"
        )

    stock = await db.stocks.find_one({"stockTicker": stock_ticker})
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    # Update user balance and portfolio
    await db.users.update_one(
        {"username": user["username"]},
        {
            "$inc": {"account.balance": -total_cost, f"portfolio.{stock_ticker}": volume},
        },
    )

    # Create transaction record
    transaction = {
        "username": user["username"],
        "orderID": order_id,
        "stockTicker": stock_ticker,
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
    responses={200: {"description": "Stock sold successfully"}},
)
async def sell_stock(stock_ticker: str, volume: int, price: float, order_id: str, user=Depends(get_current_user)):
    """
    Sells stock for the authenticated user and records a transaction.
    """
    portfolio = user.get("portfolio", {})
    if stock_ticker not in portfolio or portfolio[stock_ticker] < volume:
        raise HTTPException(
            status_code=400, detail="Insufficient holdings to complete the sale"
        )

    total_earnings = volume * price

    # Update user portfolio and balance
    await db.users.update_one(
        {"username": user["username"]},
        {
            "$inc": {"account.balance": total_earnings, f"portfolio.{stock_ticker}": -volume},
        },
    )

    # Remove stock from portfolio if quantity is zero
    user = await db.users.find_one({"username": user["username"]})
    if user["portfolio"].get(stock_ticker, 0) == 0:
        await db.users.update_one(
            {"username": user["username"]},
            {"$unset": {f"portfolio.{stock_ticker}": ""}},
        )

    # Create transaction record
    transaction = {
        "username": user["username"],
        "orderID": order_id,
        "stockTicker": stock_ticker,
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
    responses={200: {"description": "Cash deposited successfully"}},
)
async def deposit_cash(amount: float, user=Depends(get_current_user)):
    """
    Deposits cash into the authenticated user's account.
    """
    if amount <= 0:
        raise HTTPException(
            status_code=400, detail="Deposit amount must be greater than zero"
        )

    await db.users.update_one(
        {"username": user["username"]},
        {"$inc": {"account.balance": amount}},
    )

    return {"message": "Cash deposited successfully", "amount": amount}


@router.post(
    "/withdraw-cash",
    description="Withdraw cash from the account.",
    responses={200: {"description": "Cash withdrawn successfully"}},
)
async def withdraw_cash(amount: float, user=Depends(get_current_user)):
    """
    Withdraws cash from the authenticated user's account.
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
        {"username": user["username"]},
        {"$inc": {"account.balance": -amount}},
    )

    return {"message": "Cash withdrawn successfully", "amount": amount}


@router.get(
    "/portfolio",
    description="Retrieve the user's stock portfolio.",
    responses={200: {"description": "Portfolio retrieved"}},
)
async def get_user_portfolio(user=Depends(require_admin_or_self)):
    """
    Fetches the portfolio of the authenticated user.
    """
    portfolio = user.get("portfolio", {})
    return {"portfolio": portfolio}


@router.get(
    "/transactions",
    description="Retrieve the transaction history for the logged-in user.",
    responses={200: {"description": "Transaction history retrieved"}},
)
async def get_transaction_history(user=Depends(require_admin_or_self)):
    """
    Fetches the transaction history for the authenticated user.
    """
    transactions = await db.transactions.find({"username": user["username"]}).to_list(length=50)
    for txn in transactions:
        txn["id"] = str(txn["_id"])
        del txn["_id"]

    return {"transactions": transactions}
