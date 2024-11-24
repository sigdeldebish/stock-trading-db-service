from fastapi import APIRouter, HTTPException, status, Depends
from app.models.stock_model import StockCreate, StockResponse, StockUpdateRequest
from app.mongo.connector import db
from app.utils.auth_and_rbac import require_admin, get_current_user
from uuid import uuid4
from typing import Union, Any

router = APIRouter(
    prefix="/stocks",
    tags=["Stocks Operations"],
    responses={
        404: {"description": "Stock not found"},
        400: {"description": "Bad request"},
        403: {"description": "Forbidden"},
    },
)


@router.post(
    "/",
    response_model=StockResponse,
    status_code=status.HTTP_201_CREATED,
    description="Add a new stock for trading (admin-only).",
)
async def add_new_stock(stock: StockCreate, admin_user=Depends(require_admin)):
    """
    **Add New Stock:**
    - Registers a new stock for trading in the system.
    - Admin-only access.
    - Ensures the stock ticker is unique.
    """
    # Automatically assign a unique stockID if not provided
    if not stock.stockID:
        stock.stockID = str(uuid4())  # Generate a unique UUID as stockID
    # Check if stock ticker already exists
    existing_stock = await db.stocks.find_one({"stockTicker": stock.stockTicker})
    if existing_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Stock already exists", "code": "STOCK_ALREADY_EXISTS"},
        )

    stock_data = stock.dict()

    # Insert the new stock
    result = await db.stocks.insert_one(stock_data)
    stock_data["id"] = str(result.inserted_id)

    return stock_data


@router.get(
    "/{stock_ticker}",
    response_model=StockResponse,
    status_code=status.HTTP_200_OK,
    description="Retrieve details of a specific stock by its ticker.",
)
async def get_stock_details(stock_ticker: str, user=Depends(get_current_user)):
    """
    **Get Stock Details:**
    - Retrieves details of a stock by its unique ticker.
    - Accessible to all authenticated users.
    """
    stock = await db.stocks.find_one({"stockTicker": stock_ticker})

    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Stock not found", "code": "STOCK_NOT_FOUND"},
        )

    stock_data = {
        "id": str(stock["_id"]),
        "stockID": stock.get("stockID", 0),
        "stockTicker": stock["stockTicker"],
        "companyName": stock.get("companyName", "Unknown Company"),
        "volume": stock.get("volume", 0),
        "initialPrice": stock.get("initialPrice", 0.0),
        "currentPrice": stock.get("currentPrice", 0.0),
        "openingPrice": stock.get("openingPrice", stock.get("currentPrice", 0.0)),  # Default to current price
        "highPrice": stock.get("highPrice", stock.get("currentPrice", 0.0)),  # Default to current price
        "lowPrice": stock.get("lowPrice", stock.get("currentPrice", 0.0)),  # Default to current price
        "marketStatus": stock.get("marketStatus", "unknown"),  # Default to "unknown"
    }
    return stock_data


@router.put(
    "/update-price",
    response_model=StockResponse,
    status_code=status.HTTP_200_OK,
    description="Update the price of a specific stock by its ticker (admin-only).",
)
async def update_price(
    request: StockUpdateRequest,
    admin_user=Depends(require_admin),
):
    """
    **Update Price:**
    - Updates the current price of a specific stock by its ticker.
    - Admin-only access.
    """
    # Validate the new price
    if request.price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Price must be greater than 0", "code": "INVALID_PRICE"},
        )

    # Fetch the current stock details
    stock = await db.stocks.find_one({"stockTicker": request.stock_ticker})
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Stock not found", "code": "STOCK_NOT_FOUND"},
        )

    # Update highPrice and lowPrice based on the new price
    updated_data = {
        "currentPrice": request.price,
        "highPrice": max(stock.get("highPrice", request.price), request.price),
        "lowPrice": min(stock.get("lowPrice", request.price), request.price),
    }

    # Update the stock in the database
    result = await db.stocks.update_one(
        {"stockTicker": request.stock_ticker},
        {"$set": updated_data},
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Failed to update stock", "code": "UPDATE_FAILED"},
        )

    # Retrieve and format the updated stock details
    updated_stock = await db.stocks.find_one({"stockTicker": request.stock_ticker})
    stock_response = {
        "id": str(updated_stock["_id"]),
        "stockTicker": updated_stock["stockTicker"],
        "companyName": updated_stock.get("companyName", "Unknown"),
        "volume": updated_stock.get("volume", 0),
        "initialPrice": updated_stock.get("initialPrice", 0.0),
        "currentPrice": updated_stock.get("currentPrice", 0.0),
        "openingPrice": updated_stock.get("openingPrice", 0.0),
        "highPrice": updated_stock.get("highPrice", 0.0),
        "lowPrice": updated_stock.get("lowPrice", 0.0),
        "marketStatus": updated_stock.get("marketStatus", "unknown"),
    }

    return stock_response

@router.delete(
    "/{stock_ticker}",
    status_code=status.HTTP_200_OK,
    description="Remove a specific stock by its ticker (admin-only).",
)
async def remove_stock(stock_ticker: str, admin_user=Depends(require_admin)):
    """
    **Remove Stock:**
    - Deletes a specific stock from the system by its ticker.
    - Admin-only access.
    """
    result = await db.stocks.delete_one({"stockTicker": stock_ticker})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Stock not found", "code": "STOCK_NOT_FOUND"},
        )

    return {"message": "Stock removed successfully"}


@router.get(
    "/report/all",
    response_model=list[StockResponse],
    status_code=status.HTTP_200_OK,
    description="Retrieve all stocks from the database.",
)
async def get_all_stocks(user=Depends(get_current_user)):
    """
    **Get All Stocks:**
    - Retrieves all available stocks from the database.
    - Can be accessed by both customers and admin users.
    """
    # Fetch all stocks from the database
    stocks = await db.stocks.find().to_list(length=100)

    if not stocks:
        return []  # Return an empty list if no stocks are found

    # Format stock data for response
    formatted_stocks = []
    for stock in stocks:
        stock_data = {
            "id": str(stock["_id"]),
            "stockTicker": stock["stockTicker"],
            "companyName": stock.get("companyName", "Unknown Company"),
            "volume": stock.get("volume", 0),
            "currentPrice": stock.get("currentPrice", 0.0),
            "initialPrice": stock.get("initialPrice", 0.0),
            "openingPrice": stock.get("openingPrice", 0.0),
            "highPrice": stock.get("highPrice", 0.0),
            "lowPrice": stock.get("lowPrice", 0.0),
            "marketStatus": stock.get("marketStatus", "unknown"),
        }
        formatted_stocks.append(stock_data)

    return formatted_stocks
