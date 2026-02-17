from fastapi import APIRouter, Depends
from app.dependencies.roles import required_admin_role

router = APIRouter()

@router.get("/users")
def list_users():
    return {"message": "Admin access granted"}