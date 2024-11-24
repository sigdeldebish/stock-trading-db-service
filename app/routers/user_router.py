from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.models.user_model import UserSignup, UserResponse
from app.mongo.connector import db
from passlib.context import CryptContext
from app.utils.auth_and_rbac import require_admin_or_self
from app.utils.jwt_handler import create_access_token

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
    description="Register a new user as a customer or admin.",
)
async def add_user(user: UserSignup):
    """
    **Add User (Sign Up):**
    - Register a new user.
    - Hashes the password for security.
    """
    hashed_password = pwd_context.hash(user.password)

    # Check if username already exists
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"Username {user.username} already exists.", "code": "USERNAME_EXISTS"},
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

    # Generate JWT token
    token = create_access_token({"sub": user.username, "userType": user.userType})
    return {"message": "User created successfully", "token": token}


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    description="Authenticate user and return a JWT token for authenticating with other secure APIs.",
)
async def login(credentials: HTTPBasicCredentials = Depends(security)):
    """
    **Login:**
    - Authenticates a user using BasicAuth.
    - Returns a JWT token.
    """
    # Retrieve user from the database
    user_record = await db.users.find_one({"username": credentials.username})
    if not user_record or not pwd_context.verify(credentials.password, user_record["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Generate JWT token
    token = create_access_token({"sub": user_record["username"], "userType": user_record["userType"]})
    return {"message": "Login successful", "token": token}


@router.delete(
    "/{username}",
    status_code=status.HTTP_200_OK,
    description="Deactivate a user account (admin-only).",
)
async def remove_user(
    username: str,
    current_user=Depends(require_admin_or_self)
):
    """
    **Remove User:**
    - Deactivates a user account by marking it as inactive.
    """
    result = await db.users.update_one(
        {"username": username},
        {"$set": {"isActive": False}},
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"message": f"User '{username}' deactivated successfully"}


@router.put(
    "/{username}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    description="Update user details (admin or self).",
)
async def update_user_details(
    username: str,
    user: UserSignup,
    current_user=Depends(require_admin_or_self)
):
    """
    **Update User Details:**
    - Updates the username, email, or password for a user.
    """
    hashed_password = pwd_context.hash(user.password)
    update_data = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
    }
    result = await db.users.update_one(
        {"username": username},
        {"$set": update_data},
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    updated_user = await db.users.find_one({"username": user.username})
    updated_user["id"] = str(updated_user["_id"])
    del updated_user["_id"]
    return updated_user


@router.get(
    "/{username}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    description="Retrieve user details (admin or self).",
)
async def get_user_details(
    username: str,
    current_user=Depends(require_admin_or_self)
):
    """
    **Get User Details:**
    - Fetches user details by username.
    """
    user = await db.users.find_one({"username": username})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    user["id"] = str(user["_id"])
    del user["_id"]
    return user
