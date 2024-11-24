from fastapi import APIRouter, HTTPException, status, Depends
from app.mongo.connector import db
from app.utils.auth_and_rbac import require_admin

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    responses={
        403: {"description": "Admin access required"},
        404: {"description": "Resource not found"},
        400: {"description": "Bad request"},
    },
)


@router.get(
    "/verify",
    description="Verify if the user has admin privileges.",
    responses={200: {"description": "Admin verified"}},
)
async def verify_root_privileges(admin_user=Depends(require_admin)):
    """
    **Verify Root Privileges:**
    - Confirms the current user has admin privileges.
    """
    return {"message": "Admin privileges verified"}


@router.get(
    "/transactions",
    description="Retrieve all system-wide transactions.",
    responses={
        200: {"description": "System-wide transactions retrieved"},
        404: {"description": "No transactions found"},
    },
)
async def get_all_transactions(admin_user=Depends(require_admin)):
    """
    **Get All Transactions:**
    - Admin-only endpoint to fetch all transactions.
    """
    transactions = await db.transactions.find({}).to_list(length=100)
    if not transactions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "No transactions found", "code": "TRANSACTIONS_NOT_FOUND"},
        )

    for txn in transactions:
        txn["id"] = str(txn["_id"])
        del txn["_id"]

    return {"transactions": transactions}


@router.get(
    "/users",
    description="Retrieve all users in the system.",
    responses={200: {"description": "Users retrieved successfully"}},
)
async def get_all_users(admin_user=Depends(require_admin)):
    """
    **Get All Users:**
    - Admin-only endpoint to fetch all user details.
    """
    users = await db.users.find({}).to_list(length=100)
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "No users found", "code": "USERS_NOT_FOUND"},
        )

    for user in users:
        user["id"] = str(user["_id"])
        del user["_id"]

    return {"users": users}
