from app.services.cognito_service import (
    RoleChecker,
    CognitoAdminRole,
    CognitoUserRole,
)
from fastapi import Depends

required_admin_role = RoleChecker(CognitoAdminRole)
required_user_role = RoleChecker(CognitoUserRole)