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
    - Associates the order with the authenticated user.
    """
    # Ensure the user has sufficient balance (for buy orders) or portfolio (for sell orders)
    if order.orderType == "buy":
        if user["account"]["balance"] < order.volume * order.price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Insufficient balance", "code": "INSUFFICIENT_BALANCE"},
            )
    elif order.orderType == "sell":
        portfolio = user.get("portfolio", {})
        if portfolio.get(order.stockTicker, 0) < order.volume:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Insufficient stock holdings", "code": "INSUFFICIENT_STOCKS"},
            )

    # Record the order in the system with a generated timestamp
    order_data = order.dict()
    order_data["username"] = user["username"]
    order_data["timestamp"] = datetime.utcnow()  # Generate the current UTC timestamp

    result = await db.orders.insert_one(order_data)
    order_data["id"] = str(result.inserted_id)

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

    # Cancel the order
    await db.orders.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": "canceled"}})

    return {"message": "Order canceled successfully"}


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    description="Get the status of a specific order by its ID.",
    responses={
        200: {"description": "Order status retrieved successfully"},
        404: {"description": "Order not found"},
    },
)
async def get_order_status(order_id: str, user=Depends(get_current_user)):
    """
    **Get Order Status:**
    - Retrieves the current status of an order.
    - Only the order creator or an admin can access this information.
    """
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

    order["id"] = str(order["_id"])
    del order["_id"]
    return order


@router.get(
    "/all/self",
    response_model=list[OrderResponse],
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
    orders = await db.orders.find({"username": user["username"]}).to_list(length=100)
    for order in orders:
        order["id"] = str(order["_id"])
        del order["_id"]
    return orders
