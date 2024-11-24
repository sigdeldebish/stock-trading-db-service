from fastapi import APIRouter, HTTPException, status, Depends
from app.mongo.connector import db
from app.utils.auth_and_rbac import get_current_user
from app.models.order_model import OrderResponse, BuyStockRequest, SellStockRequest
from bson import ObjectId
from datetime import datetime
from fastapi.encoders import jsonable_encoder
from app.utils.utils import generate_custom_id

router = APIRouter(
	prefix="/customers",
	tags=["Customers Operations"],
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
	"/stock/buy",
	response_model=dict,
	status_code=status.HTTP_201_CREATED,
	description="Buy stock as a customer.",
	responses={
		201: {"description": "Stock purchased successfully"},
		400: {"description": "Invalid request or insufficient balance"},
		404: {"description": "Stock not found"},
	},
)
async def buy_stock(
	   buy: BuyStockRequest,
	   user=Depends(get_current_user),
):
	"""
    Buys stock for the authenticated user and records an order and transaction.
    """
	# Validate stock volume
	if buy.volume <= 0:
		raise HTTPException(
			status_code=400,
			detail={"error": "Volume must be greater than 0", "code": "INVALID_VOLUME"},
		)

	# Check market status
	market = await db.market.find_one({"marketID": 1})
	if not market or market["status"] != "open":
		raise HTTPException(
			status_code=400,
			detail={"error": "Market is closed. Transactions cannot be processed.", "code": "MARKET_CLOSED"},
		)

	# Fetch stock details
	stock = await db.stocks.find_one({"stockTicker": buy.stock_ticker})
	if not stock:
		raise HTTPException(
			status_code=404,
			detail={"error": "Stock not found", "code": "STOCK_NOT_FOUND"},
		)

	current_price = stock["currentPrice"]
	total_cost = buy.volume * current_price

	# Check user's account balance
	if user["account"]["balance"] < total_cost:
		raise HTTPException(
			status_code=400,
			detail={"error": "Insufficient balance", "code": "INSUFFICIENT_BALANCE"},
		)

	# Generate custom IDs
	order_id = generate_custom_id()
	transaction_id = generate_custom_id()

	# Create an order record
	order = {
		"orderID": order_id,
		"username": user["username"],
		"stockTicker": buy.stock_ticker,
		"orderType": "buy",
		"volume": buy.volume,
		"orderTotal": total_cost,
		"status": "completed",
		"marketStatus": stock.get("marketStatus", "open"),
		"timestamp": datetime.utcnow(),
	}
	await db.orders.insert_one(order)

	# Create a transaction record
	transaction = {
		"transactionID": transaction_id,
		"orderID": order_id,
		"username": user["username"],
		"stockTicker": buy.stock_ticker,
		"volume": buy.volume,
		"price": current_price,
		"totalPrice": total_cost,
		"transactionDate": datetime.utcnow(),
	}
	await db.transactions.insert_one(transaction)

	# Update user's account balance and portfolio
	await db.users.update_one(
		{"username": user["username"]},
		{
			"$inc": {"account.balance": -total_cost, f"portfolio.{buy.stock_ticker}": buy.volume},
		},
	)

	return {"message": "Stock purchased successfully"}


@router.post(
	"/sell/stock/",
	status_code=status.HTTP_201_CREATED,
	description="Sell stock as a customer.",
	responses={
		201: {"description": "Stock sold successfully"},
		400: {"description": "Invalid request or insufficient holdings"},
		404: {"description": "Stock not found"},
	},
)
async def sell_stock(
	   sell: SellStockRequest,
	   user=Depends(get_current_user),
):
	"""
    Sells stock for the authenticated user and records an order and transaction.
    """
	# Validate stock volume
	if sell.volume <= 0:
		raise HTTPException(
			status_code=400,
			detail={"error": "Volume must be greater than 0", "code": "INVALID_VOLUME"},
		)

	# Check market status
	market = await db.market.find_one({"marketID": 1})
	if not market or market["status"] != "open":
		raise HTTPException(
			status_code=400,
			detail={"error": "Market is closed. Transactions cannot be processed.", "code": "MARKET_CLOSED"},
		)

	# Fetch stock details
	stock = await db.stocks.find_one({"stockTicker": sell.stock_ticker})
	if not stock:
		raise HTTPException(
			status_code=404,
			detail={"error": "Stock not found", "code": "STOCK_NOT_FOUND"},
		)

	current_price = stock["currentPrice"]
	total_earnings = sell.volume * current_price

	# Check user's stock holdings
	portfolio = user.get("portfolio", {})
	if portfolio.get(sell.stock_ticker, 0) < sell.volume:
		raise HTTPException(
			status_code=400,
			detail={"error": "Insufficient stock holdings", "code": "INSUFFICIENT_HOLDINGS"},
		)

	# Generate order ID and transaction ID
	order_id = generate_custom_id()
	transaction_id = generate_custom_id()

	# Create an order record
	order = {
		"orderID": order_id,
		"username": user["username"],
		"stockTicker": sell.stock_ticker,
		"orderType": "sell",
		"volume": sell.volume,
		"orderTotal": total_earnings,
		"status": "completed",
		"marketStatus": stock.get("marketStatus", "open"),
		"timestamp": datetime.utcnow(),
	}
	await db.orders.insert_one(order)

	# Create a transaction record
	transaction = {
		"transactionID": transaction_id,
		"orderID": order_id,
		"username": user["username"],
		"stockTicker": sell.stock_ticker,
		"volume": sell.volume,
		"price": current_price,
		"totalPrice": total_earnings,
		"transactionDate": datetime.utcnow(),
	}
	await db.transactions.insert_one(transaction)

	# Update user's account balance and portfolio
	await db.users.update_one(
		{"username": user["username"]},
		{
			"$inc": {"account.balance": total_earnings, f"portfolio.{sell.stock_ticker}": -sell.volume},
		},
	)

	# Remove stock from portfolio if quantity becomes zero
	updated_portfolio = await db.users.find_one({"username": user["username"]}, {"portfolio": 1})
	if updated_portfolio and updated_portfolio["portfolio"].get(sell.stock_ticker, 0) == 0:
		await db.users.update_one(
			{"username": user["username"]},
			{"$unset": {f"portfolio.{sell.stock_ticker}": ""}},
		)

	return {"message": "Stock sold successfully"}


@router.post(
	"/deposit",
	status_code=status.HTTP_200_OK,
	description="Deposit cash into the account.",
	responses={
		200: {"description": "Cash deposited successfully"},
		400: {"description": "Invalid deposit amount"},
	},
)
async def deposit_cash(amount: float, user=Depends(get_current_user)):
	"""
    Deposits cash into the authenticated user's account, creates an order, and records a transaction.
    """
	if amount <= 0:
		raise HTTPException(
			status_code=400, detail={"error": "Deposit amount must be greater than zero", "code": "INVALID_AMOUNT"}
		)

	# Generate unique IDs
	transaction_id = ObjectId()
	order_id = ObjectId()

	# Update the user's account balance
	updated_user = await db.users.find_one_and_update(
		{"username": user["username"]},
		{"$inc": {"account.balance": amount}},
		return_document=True  # Return the updated document
	)

	if not updated_user:
		raise HTTPException(
			status_code=404, detail={"error": "User not found", "code": "USER_NOT_FOUND"}
		)

	# Create an order record for the deposit
	order = {
		"orderID": str(order_id),
		"username": user["username"],
		"orderType": "deposit",
		"volume": 0,  # No stocks involved in a cash deposit
		"orderTotal": amount,
		"status": "completed",
		"marketStatus": "N/A",  # Not applicable for deposit
		"timestamp": datetime.utcnow(),
	}
	await db.orders.insert_one(order)

	# Create a transaction record for the deposit
	transaction = {
		"transactionID": str(transaction_id),
		"orderID": str(order_id),
		"username": user["username"],
		"transactionType": "deposit",
		"amount": amount,
		"balanceAfter": updated_user["account"]["balance"],  # Updated balance
		"transactionDate": datetime.utcnow(),
	}
	await db.transactions.insert_one(transaction)

	# Prepare response
	updated_user["_id"] = str(updated_user["_id"])  # Convert MongoDB ObjectId to string
	response_content = {
		"message": "Cash deposited successfully",
		"amount": amount,
		"order": {
			"id": str(order_id),
			"orderType": "deposit",
			"orderTotal": amount,
			"status": "completed",
		},
		"transaction": str(transaction),
		"user": updated_user,
	}

	return jsonable_encoder(response_content)


@router.post(
	"/withdraw/cash",
	response_model=dict,
	status_code=status.HTTP_200_OK,
	description="Withdraw cash from the account.",
	responses={
		200: {"description": "Cash withdrawn successfully"},
		400: {"description": "Invalid withdrawal amount or insufficient balance"},
		404: {"description": "User not found"},
	},
)
async def withdraw_cash(amount: float, user=Depends(get_current_user)):
	"""
    Withdraws cash from the authenticated user's account and records a transaction.
    """
	if amount <= 0:
		raise HTTPException(
			status_code=400,
			detail={"error": "Withdrawal amount must be greater than zero", "code": "INVALID_AMOUNT"}
		)

	if user["account"]["balance"] < amount:
		raise HTTPException(
			status_code=400, detail={"error": "Insufficient balance for withdrawal", "code": "INSUFFICIENT_BALANCE"}
		)

	# Generate unique IDs
	transaction_id = ObjectId()
	order_id = ObjectId()

	# Update the user's account balance
	updated_user = await db.users.find_one_and_update(
		{"username": user["username"]},
		{"$inc": {"account.balance": -amount}},
		return_document=True
	)

	if not updated_user:
		raise HTTPException(
			status_code=404, detail={"error": "User not found", "code": "USER_NOT_FOUND"}
		)

	# Create an order record for the withdrawal
	order = {
		"orderID": order_id,
		"username": user["username"],
		"orderType": "withdrawal",
		"volume": 0,
		"orderTotal": amount,
		"status": "completed",
		"marketStatus": "N/A",
		"timestamp": datetime.utcnow(),
	}
	await db.orders.insert_one(order)

	# Create a transaction record for the withdrawal
	transaction = {
		"transactionID": transaction_id,
		"orderID": order_id,
		"username": user["username"],
		"transactionType": "withdrawal",
		"amount": amount,
		"balanceAfter": updated_user["account"]["balance"],
		"transactionDate": datetime.utcnow(),
	}
	await db.transactions.insert_one(transaction)

	# Serialize the response, converting ObjectId instances to strings
	response_content = {
		"message": "Cash withdrawn successfully",
		"amount": amount,
		"order": order,
		"transaction": transaction,
		"user": {
			"username": updated_user["username"],
			"account": {
				"balance": updated_user["account"]["balance"]
			}
		},
	}

	# Ensure all ObjectId instances are converted to strings
	def convert_object_id(data):
		if isinstance(data, ObjectId):
			return str(data)
		elif isinstance(data, list):
			return [convert_object_id(item) for item in data]
		elif isinstance(data, dict):
			return {key: convert_object_id(value) for key, value in data.items()}
		return data

	# Apply conversion to the entire response
	response_content = convert_object_id(response_content)

	return response_content


@router.get(
	"/portfolio",
	description="Retrieve the user's stock portfolio.",
	responses={200: {"description": "Portfolio retrieved"}},
)
async def get_user_portfolio(user=Depends(get_current_user)):
	"""
    Fetches the portfolio of the authenticated user.
    """
	portfolio = user.get("portfolio", {})
	return {"portfolio": portfolio}


@router.get(
	"/account/details",
	status_code=status.HTTP_200_OK,
	description="Retrieve the authenticated customer's portfolio and account details.",
	responses={
		200: {"description": "Customer details retrieved successfully"},
		404: {"description": "Customer not found"},
	},
)
async def get_customer_details(user=Depends(get_current_user)):
	"""
    Fetches the portfolio and account details for the authenticated customer.
    """
	if user["userType"] != "customer":
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail={"error": "Only customers can access this endpoint", "code": "FORBIDDEN_ACCESS"},
		)

	# Fetch user's account and portfolio details
	customer = await db.users.find_one({"username": user["username"]}, {"account": 1, "portfolio": 1})
	if not customer:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail={"error": "Customer not found", "code": "CUSTOMER_NOT_FOUND"},
		)

	# Prepare the response
	account = customer.get("account", {})
	portfolio = customer.get("portfolio", {})

	# Include portfolio details for user-friendly representation
	portfolio_details = []
	for stock_ticker, volume in portfolio.items():
		stock = await db.stocks.find_one({"stockTicker": stock_ticker}, {"companyName": 1, "currentPrice": 1})
		if stock:
			portfolio_details.append({
				"stockTicker": stock_ticker,
				"companyName": stock["companyName"],
				"volume": volume,
				"currentPrice": stock["currentPrice"],
				"totalValue": volume * stock["currentPrice"],
			})

	return {
		"account": account,
		"portfolio": portfolio_details,
	}
