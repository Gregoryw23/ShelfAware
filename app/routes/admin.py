from fastapi import APIRouter, Depends
from app.dependencies.roles import required_admin_role

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(required_admin_role)]
)

@router.get("/users")
def list_users():
    return {"message": "Admin access granted"}