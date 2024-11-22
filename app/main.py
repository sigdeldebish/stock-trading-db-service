from fastapi import FastAPI
from app.routers.router import router

app = FastAPI(
	title="Stock Trading System Group 28 RestFul Database Service",
	description="The app is a hosts APIs to make CRUD operations with attached MongoDB. "
			  "The database and service are attached and scales together",
)

# Include the router
app.include_router(router)

if __name__ == '__main__':
	if __name__ == "__main__":
		import uvicorn

		uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
