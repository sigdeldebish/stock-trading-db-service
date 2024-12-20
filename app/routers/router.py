from fastapi import APIRouter

from app.routers.user_router import router as user_router
from app.routers.stock_router import router as stock_router
from app.routers.order_router import router as order_router
from app.routers.market_router import router as market_router
from app.routers.customer_router import router as customer_router

main_router = APIRouter()

# Include individual routers
main_router.include_router(user_router)
main_router.include_router(stock_router)
main_router.include_router(order_router)
main_router.include_router(market_router)
main_router.include_router(customer_router)

