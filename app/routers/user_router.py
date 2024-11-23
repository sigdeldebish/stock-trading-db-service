from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.models.user_model import UserSignup, UserResponse
from app.mongo.connector import db
from passlib.context import CryptContext
from bson import ObjectId
from app.utils.auth_and_rbac import require_admin_or_self, require_admin

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={
        404: {"description": "User not found"},
        400: {"description": "Bad request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBasic()


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    description="Register a new user as a customer or admin (admin-only).",
    responses={201: {"description": "User created successfully"}, 400: {"description": "Username already exists"}},
)
async def add_user(user: UserSignup, admin_user=Depends(require_admin)):
    """
    **Add User (Sign Up):**
    - Admin-only endpoint for registering a new user.
    - `userType` specifies whether the user is a `customer` or an `admin`.
    - Hashes the password for security.
    """
    hashed_password = pwd_context.hash(user.password)

    # Check if username already exists
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Username already exists", "code": "USERNAME_EXISTS"},
        )

    # Insert new user
    new_user = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "userType": user.userType,  # 'customer' or 'admin'
        "account": {"balance": 0.0} if user.userType == "customer" else None,
        "portfolio": {} if user.userType == "customer" else None,
        "isActive": True,
    }
    result = await db.users.insert_one(new_user)
    return {"message": "User created successfully", "userID": str(result.inserted_id)}


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    description="Deactivate a user account (admin-only).",
    responses={200: {"description": "User deactivated successfully"}},
)
async def remove_user(user_id: str, admin_user=Depends(require_admin)):
    """
    **Remove User:**
    - Deactivates a user account by marking it as inactive.
    - Does not delete the user for historical recordkeeping.
    """
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"isActive": False}},
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "User not found", "code": "USER_NOT_FOUND"},
        )

    return {"message": "User deactivated successfully"}


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    description="Update user details (admin or self).",
    responses={200: {"description": "User details updated successfully"}},
)
async def update_user_details(user_id: str, user: UserSignup, current_user=Depends(require_admin_or_self)):
    """
    **Update User Details:**
    - Updates the username, email, or password for a user.
    - Accessible by admin users or the user themselves.
    """
    hashed_password = pwd_context.hash(user.password)
    update_data = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
    }
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data},
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "User not found", "code": "USER_NOT_FOUND"},
        )

    updated_user = await db.users.find_one({"_id": ObjectId(user_id)})
    updated_user["id"] = str(updated_user["_id"])
    del updated_user["_id"]
    return updated_user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    description="Retrieve user details (admin or self).",
    responses={200: {"description": "User details retrieved successfully"}},
)
async def get_user_details(user_id: str, current_user=Depends(require_admin_or_self)):
    """
    **Get User Details:**
    - Fetches user details by user ID.
    - Accessible by admin users or the user themselves.
    """
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "User not found", "code": "USER_NOT_FOUND"},
        )
    user["id"] = str(user["_id"])
    del user["_id"]
    return user
