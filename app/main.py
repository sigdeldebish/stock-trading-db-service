from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.router import main_router
from app.mongo.connector import initialize_collections, insert_sample_data
import os

# Create the FastAPI application
app = FastAPI(
    title="Stock Trading System - Group 28",
    description=(
        "A RESTful API service for performing CRUD operations with an attached MongoDB database. "
        "The system supports stock trading with scalable database and service architecture."
    ),
    version="1.0.0",
    docs_url="/docs",
)

# Add CORS middleware (optional for development/staging)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """
    Startup event handler for initializing collections and inserting sample data.
    Checks for the environment mode to decide whether to connect to MongoDB.
    """
    env_mode = os.getenv("TESTING", None)

    if not env_mode:
        print("Starting in production mode: Initializing MongoDB...")
        try:
            # Initialize MongoDB collections
            await initialize_collections()

            # Insert sample data
            await insert_sample_data()
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise
    else:
        print("Starting in testing mode: Skipping MongoDB initialization.")


# Include the main router
app.include_router(main_router)

# Entry point for running the app
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable hot reload for development/staging
        log_level="info",
    )
