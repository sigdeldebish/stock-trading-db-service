from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from bson import ObjectId
from app.mongo.connector import db

# Secret Key and Algorithm for JWT
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"


async def get_current_user(token: str):
	"""
    Retrieves the currently authenticated user using JWT.
    """
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		username = payload.get("sub")
		if username is None:
			raise HTTPException(
				status_code=status.HTTP_401_UNAUTHORIZED,
				detail="Invalid token",
				headers={"WWW-Authenticate": "Bearer"},
			)

		user = await db.users.find_one({"username": username})
		if not user:
			raise HTTPException(
				status_code=status.HTTP_401_UNAUTHORIZED,
				detail="User not found",
				headers={"WWW-Authenticate": "Bearer"},
			)

		if not user.get("isActive", True):
			raise HTTPException(
				status_code=status.HTTP_403_FORBIDDEN,
				detail="User account is inactive",
			)

		return user

	except JWTError:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid token",
			headers={"WWW-Authenticate": "Bearer"},
		)


async def require_admin_or_self(
	   resource_id: str,
	   current_user: dict = Depends(get_current_user)
):
	"""
    Ensures the current user is either an admin or the owner of the resource.
    """
	# Admin users have full access
	if current_user["userType"] == "admin":
		return current_user

	# For non-admins, check ownership of the resource
	resource = await db.orders.find_one({"_id": ObjectId(resource_id)})
	if not resource:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Resource not found",
		)

	if resource["userID"] != current_user["userID"]:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Access denied",
		)

	return current_user


async def require_admin(current_user: dict = Depends(get_current_user)):
	"""
    Ensures the current user is an admin.
    """
	if current_user["userType"] != "admin":
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Admin access required",
		)
	return current_user
