from fastapi import Depends, HTTPException, status, Header
from jose import JWTError, jwt
from bson import ObjectId
from app.mongo.connector import db
from app.utils.jwt_handler import verify_access_token

# Secret Key and Algorithm for JWT
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"


async def get_current_user(authorization: str = Header(..., description="JWT Authorization token")):
    """
    Retrieves the currently authenticated user using JWT.
    Dynamically fetches the Authorization header, so it does not show up in the schema.
    """
    # Extract and validate the token from the Authorization header
    token_prefix = "Bearer "
    if not authorization.startswith(token_prefix):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
        )
    token = authorization[len(token_prefix) :]
    payload = verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # Fetch the user from the database
    current_user = await db.users.find_one({"username": payload["sub"]})
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not current_user.get("isActive", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return current_user


async def require_admin_or_self(
    resource_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Ensures the current user is either an admin or the owner of the resource.
    Dynamically validates the token and resource ownership without exposing params in schema.
    """
    # Admin users have full access
    if current_user["userType"] == "admin":
        return current_user

    # For non-admins, validate ownership of the resource
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
