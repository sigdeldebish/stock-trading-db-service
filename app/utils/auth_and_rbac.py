from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from bson import ObjectId
from app.mongo.connector import db
from passlib.context import CryptContext

# Set up password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBasic()


async def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Retrieves the currently authenticated user using HTTP Basic Authentication.
    """
    # Find the user in the database
    user = await db.users.find_one({"username": credentials.username})

    if not user or not pwd_context.verify(credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid username or password", "code": "INVALID_CREDENTIALS"},
            headers={"WWW-Authenticate": "Basic"},
        )

    if not user.get("isActive", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "User account is inactive", "code": "ACCOUNT_INACTIVE"},
        )

    return user


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
            detail={"error": "Resource not found", "code": "RESOURCE_NOT_FOUND"},
        )

    if resource["userID"] != current_user["userID"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Access denied", "code": "ACCESS_DENIED"},
        )

    return current_user


async def require_admin(current_user: dict = Depends(get_current_user)):
    """
    Ensures the current user is an admin.
    """
    if current_user["userType"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Admin access required", "code": "ADMIN_ACCESS_REQUIRED"},
        )
    return current_user
