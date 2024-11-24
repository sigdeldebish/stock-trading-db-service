from fastapi import APIRouter, HTTPException, status, Depends
from app.models.order_model import OrderCreate, OrderResponse
from app.mongo.connector import db
from bson import ObjectId
from app.utils.auth_and_rbac import get_current_user
from datetime import datetime

router = APIRouter(
	prefix="/orders",
	tags=["Orders Operations"],
	responses={
		404: {"description": "Order not found"},
		403: {"description": "Forbidden"},
		400: {"description": "Bad request"},
	},
)


@router.post(
	"/",
	response_model=OrderResponse,
	status_code=status.HTTP_201_CREATED,
	description="Place a new order for buying or selling stocks.",
	responses={
		201: {"description": "Order placed successfully"},
		400: {"description": "Invalid order data"},
	},
)
async def execute_order(order: OrderCreate, user=Depends(get_current_user)):
	"""
    **Execute Order:**
    - Places a new order for buying or selling stocks.
    - Associates the order with the authenticated user using the username.
    """
	# Ensure the stock exists
	stock = await db.stocks.find_one({"stockTicker": order.stockTicker})
	if not stock:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail={"error": "Stock not found", "code": "STOCK_NOT_FOUND"},
		)

	# Fetch the current price of the stock
	current_price = stock["currentPrice"]

	# Calculate the total order value
	total_price = current_price * order.volume

	# Ensure the user has sufficient balance (for buy orders) or portfolio (for sell orders)
	if order.orderType == "buy":
		if user["account"]["balance"] < total_price:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail={"error": "Insufficient balance", "code": "INSUFFICIENT_BALANCE"},
			)
		# Deduct balance
		updated_balance = user["account"]["balance"] - total_price
		await db.users.update_one(
			{"username": user["username"]},
			{"$set": {"account.balance": updated_balance}},
		)
	elif order.orderType == "sell":
		portfolio = user.get("portfolio", {})
		if portfolio.get(order.stockTicker, 0) < order.volume:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail={"error": "Insufficient stock holdings", "code": "INSUFFICIENT_STOCKS"},
			)
		# Update portfolio
		updated_portfolio = portfolio[order.stockTicker] - order.volume
		await db.users.update_one(
			{"username": user["username"]},
			{
				"$set": {
					f"portfolio.{order.stockTicker}": updated_portfolio,
					# Ensure balance is updated for a sell order
					"account.balance": user["account"]["balance"] + total_price,
				}
			},
		)

	# Create the order record
	order_data = order.dict()
	order_data["username"] = user["username"]
	order_data["order_total"] = total_price
	order_data["timestamp"] = datetime.utcnow()

	# Insert the order into the database
	result = await db.orders.insert_one(order_data)
	order_data["id"] = str(result.inserted_id)

	# Create a transaction for the order
	transaction_data = {
		"orderID": order_data["orderID"],
		"username": user["username"],
		"stockTicker": order.stockTicker,
		"volume": order.volume,
		"price": current_price,
		"totalPrice": total_price,
		"transactionDate": datetime.utcnow(),
	}
	await db.transactions.insert_one(transaction_data)

	# Mark the order as completed
	await db.orders.update_one(
		{"_id": result.inserted_id},
		{"$set": {"status": "completed"}},
	)
	order_data["status"] = "completed"

	return order_data


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_200_OK,
    description="Cancel an order by its ID.",
    responses={
        200: {"description": "Order canceled successfully"},
        404: {"description": "Order not found"},
    },
)
async def cancel_order(order_id: str, user=Depends(get_current_user)):
    """
    **Cancel Order:**
    - Cancels an order.
    - Only the order creator or an admin can cancel the order.
    - Updates the user's portfolio and account balance accordingly.
    """
    # Check if the order exists
    order = await db.orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Order not found", "code": "ORDER_NOT_FOUND"},
        )

    # Check if the current user is allowed to cancel the order
    if user["userType"] != "admin" and order["username"] != user["username"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    # Ensure the order is not already completed or canceled
    if order["status"] in ["completed", "canceled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Cannot cancel a completed or already canceled order", "code": "INVALID_ORDER_STATUS"},
        )

    # Update the user's portfolio and account balance
    if order["orderType"] == "buy":
        # For buy orders, refund the total amount to the user's account balance
        refund_amount = order["orderTotal"]
        await db.users.update_one(
            {"username": user["username"]},
            {"$inc": {"account.balance": refund_amount}}
        )
    elif order["orderType"] == "sell":
        # For sell orders, restore the stock volume back to the user's portfolio
        stock_ticker = order["stockTicker"]
        volume = order["volume"]
        await db.users.update_one(
            {"username": user["username"]},
            {"$inc": {f"portfolio.{stock_ticker}": volume}}
        )

    # Cancel the order
    await db.orders.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": "canceled"}})

    return {"message": "Order canceled successfully"}


@router.get(
    "/{order_id}",
    response_model=dict,  # No schema enforcement to avoid validation issues
    status_code=status.HTTP_200_OK,
    description="Get the order by its ID.",
    responses={
        200: {"description": "Order status retrieved successfully"},
        404: {"description": "Order not found"},
    },
)
async def get_order_by_id(order_id: str, user=Depends(get_current_user)):
    """
    **Get Order Status:**
    - Retrieves the current status of an order.
    - Only the order creator or an admin can access this information.
    """
    try:
        # Fetch the order from the database
        order = await db.orders.find_one({"_id": ObjectId(order_id)})

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Order not found", "code": "ORDER_NOT_FOUND"},
            )

        # Check if the current user is allowed to view the order status
        if user["userType"] != "admin" and order["username"] != user["username"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied.",
            )

        # Format the order response
        formatted_order = {
            "id": str(order["_id"]),  # Convert ObjectId to string
            "username": order.get("username"),
            "orderType": order.get("orderType"),
            "status": order.get("status"),
            "marketStatus": order.get("marketStatus"),
            "timestamp": order.get("timestamp"),
        }

        # Add fields based on the order type
        if order["orderType"] in ["buy", "sell"]:
            formatted_order.update({
                "stockTicker": order.get("stockTicker"),
                "volume": order.get("volume"),
                "orderTotal": order.get("orderTotal"),
            })
        elif order["orderType"] in ["deposit", "withdrawal"]:
            formatted_order.update({
                "amount": order.get("amount"),
                "balanceAfter": order.get("balanceAfter"),
            })

        return formatted_order

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to fetch the order", "exception": str(e)},
        )


@router.get(
    "/all/self",
    response_model=list[dict],
    status_code=status.HTTP_200_OK,
    description="Retrieve a list of past orders for the authenticated user.",
    responses={
        200: {"description": "Past orders retrieved successfully"},
    },
)
async def get_past_orders(user=Depends(get_current_user)):
    """
    **Get All Orders for User:**
    - Fetches a list of all past orders placed by the authenticated user.
    """
    try:
        # Fetch orders for the authenticated user
        orders = await db.orders.find({"username": user["username"]}).to_list(length=100)

        # Simplify transformation and keep only relevant fields
        formatted_orders = []
        for order in orders:
            formatted_orders.append({
                "id": str(order["_id"]),  # Convert MongoDB ObjectId to string for `id`
                "username": order.get("username"),
                "stockTicker": order.get("stockTicker"),
                "orderType": order.get("orderType"),
                "volume": order.get("volume"),
                "status": order.get("status", "pending"),
                "marketStatus": order.get("marketStatus", "unknown"),
                "order_total": order.get("order_total", 0),
                "orderID": str(order.get("orderID", ""))  # Convert ObjectId or keep as string
            })

        return formatted_orders

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to fetch orders", "exception": str(e)},
        )
