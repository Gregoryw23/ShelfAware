from fastapi import APIRouter, Depends
from app.services.cognito_service import RoleChecker, CognitoAdminRole

router = APIRouter()

@router.get("/users", dependencies=[Depends(RoleChecker("Admins"))])
def list_users():
    return {"message": "Admin access granted"}