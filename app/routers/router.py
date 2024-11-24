from fastapi import APIRouter

from app.routers.user_router import router as user_router
from app.routers.stock_router import router as stock_router
from app.routers.order_router import router as order_router
from app.routers.transaction_router import router as transaction_router
from app.routers.market_router import router as market_router

main_router = APIRouter()

# Include individual routers
main_router.include_router(user_router, tags=["Users Operations"])
main_router.include_router(stock_router, tags=["Stocks Operations"])
main_router.include_router(order_router, tags=["Orders Operations"])
main_router.include_router(transaction_router, tags=["Transactions Operations"])
main_router.include_router(market_router, tags=["Market Operations"])
