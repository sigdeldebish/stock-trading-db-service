from fastapi import APIRouter, HTTPException, status, Depends
from app.models.stock_model import StockCreate, StockResponse
from app.mongo.connector import db
from bson import ObjectId
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
    responses={
        201: {"description": "Stock added successfully"},
        400: {"description": "Stock already exists"},
        403: {"description": "Admin access required"},
    },
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
    "/{stock_id}",
    response_model=StockResponse,
    status_code=status.HTTP_200_OK,
    description="Retrieve details of a specific stock by its ID (open to all authenticated users).",
    responses={
        200: {"description": "Stock retrieved successfully"},
        404: {"description": "Stock not found"},
    },
)
async def get_stock_details(stock_id: str, user=Depends(get_current_user)):
    """
    **Get Stock Details:**
    - Retrieves details of a stock by its unique ID.
    - Accessible to all authenticated users.
    """
    stock = await db.stocks.find_one({"_id": ObjectId(stock_id)})

    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Stock not found", "code": "STOCK_NOT_FOUND"},
        )

    stock["id"] = str(stock["_id"])
    del stock["_id"]
    return stock


@router.put(
    "/{stock_id}/price",
    response_model=StockResponse,
    status_code=status.HTTP_200_OK,
    description="Update the price of a specific stock (admin-only).",
    responses={
        200: {"description": "Stock price updated successfully"},
        404: {"description": "Stock not found"},
        400: {"description": "Invalid price"},
        403: {"description": "Admin access required"},
    },
)
async def update_price(stock_id: str, price: float, admin_user=Depends(require_admin)):
    """
    **Update Price:**
    - Updates the current price of a specific stock.
    - Admin-only access.
    """
    if price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Price must be greater than 0", "code": "INVALID_PRICE"},
        )

    result = await db.stocks.update_one(
        {"_id": ObjectId(stock_id)},
        {"$set": {"currentPrice": price}},
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Stock not found", "code": "STOCK_NOT_FOUND"},
        )

    updated_stock = await db.stocks.find_one({"_id": ObjectId(stock_id)})
    updated_stock["id"] = str(updated_stock["_id"])
    del updated_stock["_id"]
    return updated_stock


@router.delete(
    "/{stock_id}",
    status_code=status.HTTP_200_OK,
    description="Remove a specific stock from the system (admin-only).",
    responses={
        200: {"description": "Stock removed successfully"},
        404: {"description": "Stock not found"},
        403: {"description": "Admin access required"},
    },
)
async def remove_stock(stock_id: str, admin_user=Depends(require_admin)):
    """
    **Remove Stock:**
    - Deletes a specific stock from the system.
    - Admin-only access.
    """
    result = await db.stocks.delete_one({"_id": ObjectId(stock_id)})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Stock not found", "code": "STOCK_NOT_FOUND"},
        )

    return {"message": "Stock removed successfully"}
