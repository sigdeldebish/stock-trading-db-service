from fastapi import APIRouter, HTTPException, status, Depends
from app.models.stock_model import StockCreate, StockResponse
from app.mongo.connector import db
from app.utils.auth_and_rbac import require_admin, get_current_user

router = APIRouter(
    prefix="/stocks",
    tags=["Stocks"],
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

    stock["id"] = str(stock["_id"])
    del stock["_id"]
    return stock


@router.put(
    "/{stock_ticker}/price",
    response_model=StockResponse,
    status_code=status.HTTP_200_OK,
    description="Update the price of a specific stock by its ticker (admin-only).",
)
async def update_price(stock_ticker: str, price: float, admin_user=Depends(require_admin)):
    """
    **Update Price:**
    - Updates the current price of a specific stock by its ticker.
    - Admin-only access.
    """
    if price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Price must be greater than 0", "code": "INVALID_PRICE"},
        )

    result = await db.stocks.update_one(
        {"stockTicker": stock_ticker},
        {"$set": {"currentPrice": price}},
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Stock not found", "code": "STOCK_NOT_FOUND"},
        )

    updated_stock = await db.stocks.find_one({"stockTicker": stock_ticker})
    updated_stock["id"] = str(updated_stock["_id"])
    del updated_stock["_id"]
    return updated_stock


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
