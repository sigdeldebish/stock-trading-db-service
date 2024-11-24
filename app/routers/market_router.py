from fastapi import APIRouter, HTTPException, status, Depends
from app.models.market_model import MarketUpdate, MarketResponse
from app.mongo.connector import db
from app.utils.auth_and_rbac import require_admin, get_current_user
from datetime import datetime

router = APIRouter(
    prefix="/market",
    tags=["Market"],
    responses={
        404: {"description": "Market not found"},
        400: {"description": "Bad request"},
        403: {"description": "Forbidden"},
    },
)


@router.put(
    "/status",
    response_model=MarketResponse,
    status_code=status.HTTP_200_OK,
    description="Update the market's status, opening hours, or holidays (admin-only).",
)
async def update_market_status(
    market_update: MarketUpdate, admin_user=Depends(require_admin)
):
    """
    **Update Market Status:**
    - Allows admins to modify the market's status (open/closed), opening hours, or holiday list.
    """
    update_data = {k: v for k, v in market_update.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "No valid fields provided for update", "code": "NO_VALID_FIELDS"},
        )

    result = await db.market.update_one({"marketID": 1}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Market not found", "code": "MARKET_NOT_FOUND"},
        )

    market = await db.market.find_one({"marketID": 1})
    market["id"] = str(market["_id"])
    del market["_id"]
    return market


@router.get(
    "/",
    response_model=MarketResponse,
    status_code=status.HTTP_200_OK,
    description="Retrieve the current market status, opening hours, and holidays.",
)
async def get_market_status(user=Depends(get_current_user)):
    """
    **Get Market Status:**
    - Allows all authenticated users to retrieve the current market status.
    """
    market = await db.market.find_one({"marketID": 1})
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Market not found", "code": "MARKET_NOT_FOUND"},
        )
    market["id"] = str(market["_id"])
    del market["_id"]
    return market


@router.put(
    "/open",
    status_code=status.HTTP_200_OK,
    description="Open the market (admin-only).",
)
async def open_market(admin_user=Depends(require_admin)):
    """
    **Open Market:**
    - Admin-only endpoint to open the market.
    """
    result = await db.market.update_one({"marketID": 1}, {"$set": {"status": "open"}})
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Market not found", "code": "MARKET_NOT_FOUND"},
        )
    return {"message": "Market opened successfully"}


@router.put(
    "/close",
    status_code=status.HTTP_200_OK,
    description="Close the market (admin-only).",
)
async def close_market(admin_user=Depends(require_admin)):
    """
    **Close Market:**
    - Admin-only endpoint to close the market.
    """
    result = await db.market.update_one({"marketID": 1}, {"$set": {"status": "closed"}})
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Market not found", "code": "MARKET_NOT_FOUND"},
        )
    return {"message": "Market closed successfully"}


@router.put(
    "/schedule",
    response_model=MarketResponse,
    status_code=status.HTTP_200_OK,
    description="Update the market's schedule (opening and closing hours, admin-only).",
)
async def update_market_schedule(
    opening_hours: str,
    closing_hours: str,
    admin_user=Depends(require_admin),
):
    """
    **Update Market Schedule:**
    - Admin-only endpoint to update market opening and closing hours.
    """
    result = await db.market.update_one(
        {"marketID": 1},
        {"$set": {"openingHours": opening_hours, "closingHours": closing_hours}},
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Market not found", "code": "MARKET_NOT_FOUND"},
        )

    market = await db.market.find_one({"marketID": 1})
    market["id"] = str(market["_id"])
    del market["_id"]
    return market


@router.get(
    "/is-open",
    status_code=status.HTTP_200_OK,
    description="Check if the market is open (accessible to all authenticated users).",
)
async def is_market_open(user=Depends(get_current_user)):
    """
    **Is Market Open:**
    - Checks whether the market is currently open.
    """
    market = await db.market.find_one({"marketID": 1})
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Market not found", "code": "MARKET_NOT_FOUND"},
        )

    current_time = datetime.now().strftime("%H:%M")
    if (
        market["status"] == "open"
        and market["openingHours"] <= current_time <= market["closingHours"]
    ):
        return {"isMarketOpen": True}
    return {"isMarketOpen": False}
