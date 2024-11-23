from motor.motor_asyncio import AsyncIOMotorClient
import os

# MongoDB Connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client["stock_trading_db"]

# Collection Names
USERS_COLLECTION = "users"
TRANSACTIONS_COLLECTION = "transactions"
STOCKS_COLLECTION = "stocks"
ORDERS_COLLECTION = "orders"
MARKET_COLLECTION = "market"
ACCOUNTS_COLLECTION = "accounts"  # Added for customer accounts


async def initialize_collections():
    """
    Initialize MongoDB collections and indexes.
    Ensures indexes are created for proper query performance.
    """
    # Users Collection
    await db[USERS_COLLECTION].create_index("userID", unique=True)
    await db[USERS_COLLECTION].create_index("username", unique=True)
    await db[USERS_COLLECTION].create_index("email", unique=True)

    # Accounts Collection
    await db[ACCOUNTS_COLLECTION].create_index("accountID", unique=True)
    await db[ACCOUNTS_COLLECTION].create_index("userID", unique=True)  # Enforce one-to-one relationship

    # Transactions Collection
    await db[TRANSACTIONS_COLLECTION].create_index("transactionID", unique=True)
    await db[TRANSACTIONS_COLLECTION].create_index("userID")
    await db[TRANSACTIONS_COLLECTION].create_index("accountID")  # To link to accounts
    await db[TRANSACTIONS_COLLECTION].create_index("stockID")

    # Stocks Collection
    await db[STOCKS_COLLECTION].create_index("stockID", unique=True)
    await db[STOCKS_COLLECTION].create_index("stockTicker", unique=True)

    # Orders Collection
    await db[ORDERS_COLLECTION].create_index("orderID", unique=True)
    await db[ORDERS_COLLECTION].create_index("userID")

    # Market Collection
    await db[MARKET_COLLECTION].create_index("marketID", unique=True)


async def insert_sample_data():
    """
    Insert sample data into the database for testing purposes.
    Skips insertion if the data already exists.
    """
    # Sample Users
    sample_users = [
        {
            "userID": 1,
            "username": "admin_user",
            "email": "admin@example.com",
            "password": "hashed_admin_password",  # Replace with hashed password
            "userType": "admin",
            "account": None,
            "portfolio": None,
            "isActive": True,
        },
        {
            "userID": 2,
            "username": "customer_user",
            "email": "customer@example.com",
            "password": "hashed_customer_password",  # Replace with hashed password
            "userType": "customer",
            "account": {"accountID": 101, "balance": 10000.0},
            "portfolio": {"1": 50, "2": 20},  # Example: StockID -> Shares Owned
            "isActive": True,
        },
    ]
    for user in sample_users:
        existing_user = await db[USERS_COLLECTION].find_one({"userID": user["userID"]})
        if not existing_user:
            await db[USERS_COLLECTION].insert_one(user)

    # Sample Accounts
    sample_accounts = [
        {
            "accountID": 101,
            "userID": 2,  # Linked to the customer user
            "balance": 10000.0,
        }
    ]
    for account in sample_accounts:
        existing_account = await db[ACCOUNTS_COLLECTION].find_one({"accountID": account["accountID"]})
        if not existing_account:
            await db[ACCOUNTS_COLLECTION].insert_one(account)

    # Sample Stocks
    sample_stocks = [
        {
            "stockID": 1,
            "stockTicker": "AAPL",
            "companyName": "Apple Inc.",
            "volume": 100000,
            "initialPrice": 150.0,
            "currentPrice": 150.0,
        },
        {
            "stockID": 2,
            "stockTicker": "GOOG",
            "companyName": "Alphabet Inc.",
            "volume": 50000,
            "initialPrice": 2800.0,
            "currentPrice": 2800.0,
        },
    ]
    for stock in sample_stocks:
        existing_stock = await db[STOCKS_COLLECTION].find_one({"stockID": stock["stockID"]})
        if not existing_stock:
            await db[STOCKS_COLLECTION].insert_one(stock)

    # Sample Market Data
    market_data = {
        "marketID": 1,
        "status": "open",
        "openingHours": "09:00",
        "closingHours": "16:00",
        "holidays": ["2024-12-25", "2024-01-01"],
    }
    existing_market = await db[MARKET_COLLECTION].find_one({"marketID": market_data["marketID"]})
    if not existing_market:
        await db[MARKET_COLLECTION].insert_one(market_data)

    print("Sample data inserted successfully.")
