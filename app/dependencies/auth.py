from app.services.cognito_service import RoleChecker, CognitoAdminRole, CognitoUserRole

required_admin_role = RoleChecker(CognitoAdminRole)
required_user_role = RoleChecker(CognitoUserRole)

#Additional part for bookshelf service:
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User

def get_current_user(
    db: Session = Depends(get_db),
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    user = db.query(User).filter(User.user_id == x_user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")
    return user